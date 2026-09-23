#!/bin/bash
# Start the full Sentinel stack: llama.cpp backend (:8912) + /v1/systemone proxy (:8915)
if ! curl -s --max-time 2 http://127.0.0.1:8912/health | grep -q ok; then
  setsid nohup /home/cactus/code/llama.cpp/build-vk2/bin/llama-server \
    -m /home/cactus/models/gguf38/Qwen3.8-27B-UD-Q4_K_M.gguf \
    --port 8912 -ngl 999 -c 8192 --jinja > /home/cactus/jev-runs/llama-server-sentinel.log 2>&1 < /dev/null &
  echo -n "waiting for backend"
  for i in $(seq 1 60); do curl -s --max-time 2 http://127.0.0.1:8912/health | grep -q ok && break; echo -n .; sleep 5; done
  echo
fi
if ! curl -s --max-time 2 http://127.0.0.1:8915/health | grep -q 'ok'; then
  setsid nohup /home/cactus/ml-venv/bin/python /home/cactus/jev-runs/sentinel_server.py \
    > /home/cactus/jev-runs/sentinel.log 2>&1 < /dev/null &
  sleep 4
fi
curl -s http://127.0.0.1:8915/health && echo " <- sentinel ready (8915)"
