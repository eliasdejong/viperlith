#!/bin/bash
set -euo pipefail
trap 'kill -KILL -$$' TERM INT EXIT

if [ -f .env ]; then
	set -a; source .env; set +a
fi

export PATH="$(pwd)/.venv/bin:$PATH"
export PYTHONPATH=.
export DEBUG="${DEBUG:-1}"
export WEB_CONCURRENCY=$(( DEBUG == 1 ? 1 : $(nproc) ))

python src/util/db_migration.py
python src/util/mpsc_queue.py

if [ "$DEBUG" -eq 1 ]; then
	watchfiles "python src/single_writer.py" . &
	uvicorn src.web_worker:app --loop uvloop --reload --log-level debug &
else
	python src/single_writer.py &
	uvicorn src.web_worker:app --loop uvloop --host 0.0.0.0 --port 8000 --log-level warning --no-access-log &
fi

wait -n