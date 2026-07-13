#!/bin/bash
trap 'kill -KILL -$$' EXIT

set -a; source .env; set +a

export DEBUG="1"

uv run watchfiles "python src/writer.py" . &
uv run uvicorn src.main:app --loop uvloop --reload --log-level debug &

wait