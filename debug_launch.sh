#!/bin/bash
trap 'kill -TERM -$$' EXIT

set -a; source .env; set +a

export DEBUG=1
export WEB_CONCURRENCY=1

rm -f /dev/shm/datastar-gpt-cmdqueue-*

sudo mkdir -p $DB_PATH
sudo chown -R $USER:$USER $DB_PATH
uv run schema/migrate.py

uv run watchfiles "python src/writer.py" . &
uv run uvicorn src.main:app --loop uvloop --reload --log-level debug &

wait