#!/usr/bin/env python3
"""Sentinel — open System One decision server (TypeSafe /v1/systemone wire format).

POST /v1/systemone
  {"state": ..., "model": ..., "questions": {"decision": {...}}}
Question types (mirrors Jev):
  noul   {"type":"noul","instructions":str}                    -> {"noul": p_yes}
  choice {"type":"choice","instructions":str,"criteria":{opt:desc}} -> {"probabilities":{opt:p}}
  score  {"type":"score","instructions":str,"criteria":[levels]}    -> {"probabilities":{"0":p,...}}

Each decision = ONE prefill forward pass on the local llama.cpp server
(letter-logit readout at the last prompt position; no tokens are ever sampled).
Responses add "confidence" (top1-top2 gap) and "abstain" (bool) — extra fields,
wire-compatible with clients that ignore them.

Env: SENTINEL_PORT (8915), LLAMA_URL (http://127.0.0.1:8912),
     SENTINEL_TOK (tokenizer for chat template, default Qwen/Qwen3.5-4B),
     SENTINEL_TEMPERATURE (1.2, fitted on JevBench public), SENTINEL_API_KEY (optional).
"""
from __future__ import annotations

import json
import math
import os
import time
import urllib.request

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

LLAMA_URL = os.environ.get("LLAMA_URL", "http://127.0.0.1:8912")
TOK_ID = os.environ.get("SENTINEL_TOK", "Qwen/Qwen3.5-4B")
TEMPERATURE = float(os.environ.get("SENTINEL_TEMPERATURE", "1.2"))
API_KEY = os.environ.get("SENTINEL_API_KEY", "")
MODEL_NAME = os.environ.get("SENTINEL_MODEL_NAME", "sentinel-0.1-qwen38-27b")
PORT = int(os.environ.get("SENTINEL_PORT", "8915"))

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIRECT_SYSTEM = (
    "Apply the supplied criterion to the supplied evidence. Choose exactly one listed option. "
    "Respond with only its uppercase letter, with no explanation or reasoning."
)

app = FastAPI(title="Sentinel", version="0.1")
_state = {}


def _load():
    if _state:
        return _state
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(TOK_ID)
    letter_ids = {}
    for L in LETTERS:
        ids = tok.encode(L, add_special_tokens=False)
        if len(ids) == 1:
            letter_ids[L] = ids[0]
    _state["tok"] = tok
    _state["letter_ids"] = letter_ids
    return _state


def _llama_completion(prompt: str) -> dict:
    body = {"prompt": prompt, "n_predict": 1, "temperature": 0.0,
            "n_probs": 200, "cache_prompt": True}
    req = urllib.request.Request(
        f"{LLAMA_URL}/completion", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def _letter_probs(top: dict[int, float], labels: list[str]) -> tuple[dict, float]:
    """Softmax over letter logits at temperature TEMPERATURE -> label probs + top1-top2 gap."""
    s = _load()
    tok = s["tok"]; letter_ids = s["letter_ids"]
    logps = []
    for i, _l in enumerate(labels):
        tid = letter_ids.get(LETTERS[i])
        logps.append(top.get(tid, -20.0))
    t = max(TEMPERATURE, 1e-6)
    mx = max(logps)
    ws = [math.exp((x - mx) / t) for x in logps]
    z = sum(ws)
    probs = [w / z for w in ws]
    sp = sorted(probs, reverse=True)
    gap = (sp[0] - sp[1]) if len(sp) > 1 else sp[0]
    return dict(zip(labels, probs)), gap


def _top_logprobs(resp: dict) -> dict[int, float]:
    pos = resp["completion_probabilities"][0]
    out = {}
    for cand in pos.get("top_logprobs", []):
        tid = cand.get("id", cand.get("token_id"))
        lp = cand.get("logprob")
        if tid is not None and lp is not None:
            out[int(tid)] = float(lp)
    return out


def _build_prompt(question: dict, labels: list[str], descs: list[str]):
    s = _load()
    tok = s["tok"]
    payload = {
        "evidence": question.get("state"),
        "criterion": question.get("instructions"),
        "options": [{"letter": LETTERS[i], "description": d} for i, d in enumerate(descs)],
    }
    messages = [{"role": "system", "content": DIRECT_SYSTEM},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]
    return tok.apply_chat_template(messages, tokenize=False,
                                   add_generation_prompt=True, enable_thinking=False)


def _answer_one(question: dict) -> dict:
    """question: {"type","instructions","criteria","state"} -> wire answer dict."""
    qtype = question.get("type")
    if qtype == "noul":
        labels = ["no", "yes"]
        crit = question.get("criteria") or {}
        descs = [crit.get("false", "No") if isinstance(crit, dict) else "No",
                 crit.get("true", "Yes") if isinstance(crit, dict) else "Yes"]
        keymap = {"noul": None}
    elif qtype == "choice":
        crit = question.get("criteria") or {}
        labels = list(crit.keys())
        descs = [str(crit[k]) for k in labels]
    elif qtype == "score":
        crit = question.get("criteria")
        labels = [str(i) for i in range(len(crit))]
        descs = [str(c) for c in crit]
    else:
        raise ValueError(f"unknown question type {qtype}")

    prompt = _build_prompt(question, labels, descs)
    resp = _llama_completion(prompt)
    top = _top_logprobs(resp)
    probs, gap = _letter_probs(top, labels)
    toks = resp.get("tokens_evaluated", 0)

    answer: dict = {"type": qtype}
    if qtype == "choice":
        answer["choice"] = max(probs, key=probs.get)
    if qtype == "noul":
        answer["noul"] = probs["yes"]
        answer["probabilities"] = probs
    else:
        answer["probabilities"] = {k: round(v, 6) for k, v in probs.items()}
    answer["confidence"] = round(gap, 4)
    answer["abstain"] = bool(gap < float(os.environ.get("SENTINEL_ABSTAIN_GAP", "0.02")))
    return answer, toks


@app.get("/health")
def health():
    try:
        with urllib.request.urlopen(f"{LLAMA_URL}/health", timeout=3) as r:
            ok = json.loads(r.read()).get("status") == "ok"
        return {"status": "ok" if ok else "degraded", "llama": ok}
    except Exception:
        return {"status": "degraded", "llama": False}


@app.get("/v1/models")
def models():
    return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]}


@app.post("/v1/systemone")
async def systemone(req: Request):
    if API_KEY:
        auth = req.headers.get("authorization", "")
        if auth != f"Bearer {API_KEY}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
    t0 = time.perf_counter()
    try:
        body = await req.json()
        state = body.get("state")
        questions = body.get("questions") or {}
        answers = {}
        total_toks = 0
        for qname, q in questions.items():
            qfull = dict(q)
            qfull["state"] = state
            answer, toks = _answer_one(qfull)
            answers[qname] = answer
            total_toks += toks
        latency = time.perf_counter() - t0
        return {
            "model": MODEL_NAME,
            "answers": answers,
            "usage": {"input_tokens": total_toks, "output_tokens": 0},
            "latency_ms": round(latency * 1000, 1),
            "probs_source": "native_letter_logits",
            "temperature": TEMPERATURE,
        }
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
