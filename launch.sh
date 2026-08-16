#!/bin/bash
trap 'kill -KILL -$$' EXIT

set -a; source .env; set +a

export PYTHONPATH=.
export DEBUG="${DEBUG:-1}"
export WEB_CONCURRENCY=$(( DEBUG == 1 ? 1 : $(nproc) - 1 ))

uv run python -c "from src.util.db_migration import run_migration; run_migration()"
uv run python -c "from src.util.mpsc_queue import setup; setup()"

if [ "$DEBUG" -eq 1 ]; then
	uv run watchfiles "python src/single_writer.py" . &
	uv run uvicorn src.web_worker:app --loop uvloop --reload --log-level debug &
else
	uv run python src/single_writer.py &
	uv run uvicorn src.web_worker:app --loop uvloop --host 0.0.0.0 --port 8000 --log-level warning --no-access-log &
fi

wait