#!/bin/bash
set -euo pipefail
trap 'kill -KILL -$$' TERM INT

set -a; source .env; set +a

export PYTHONPATH=.
export DEBUG="${DEBUG:-1}"
export WEB_CONCURRENCY=$(( DEBUG == 1 ? 1 : $(nproc) - 1 ))

uv run src/util/db_migration.py
uv run src/util/mpsc_queue.py

if [ "$DEBUG" -eq 1 ]; then
	uv run watchfiles "python src/single_writer.py" . &
	uv run uvicorn src.web_worker:app --loop uvloop --reload --log-level debug &
else
	uv run python src/single_writer.py &
	uv run uvicorn src.web_worker:app --loop uvloop --host 0.0.0.0 --port 8000 --log-level warning --no-access-log &
fi

wait -n || true
kill -KILL -$$