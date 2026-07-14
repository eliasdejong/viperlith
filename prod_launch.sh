#!/bin/bash
trap 'kill -TERM -$$' EXIT

set -a; source .env; set +a

export DEBUG="0"
export WEB_CONCURRENCY=$(($(nproc) - 2 > 1 ? $(nproc) - 2 : 1))

rm -f /dev/shm/datastar-gpt-cmdqueue-*

uv run python src/writer.py &
uv run uvicorn src.main:app --loop uvloop --host 0.0.0.0 --port 8000 &

wait