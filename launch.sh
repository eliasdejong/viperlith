#!/bin/bash

set -a; source .env; set +a

export DEBUG="${DEBUG:-1}"

uv run schema/migrate.py

if [ "$DEBUG" -eq 1 ]; then
	export WEB_CONCURRENCY=1
	uv run watchfiles "python src/writer.py" . &
	uv run uvicorn src.main:app --loop uvloop --reload --log-level debug &
else
	export WEB_CONCURRENCY=$(($(nproc) - 1 > 1 ? $(nproc) - 1 : 1))
	uv run python src/writer.py &
	uv run uvicorn src.main:app --loop uvloop --host 0.0.0.0 --port 8000 &
fi

wait