#!/bin/bash
trap 'kill -KILL -$$' EXIT

set -a; source .env; set +a

export DEBUG="0"

uv run python src/writer.py &
uv run uvicorn src.main:app --loop uvloop --host 0.0.0.0 --port 8000 &

wait