#!/bin/bash
trap 'kill -TERM -$$' EXIT

set -a; source .env; set +a

export DEBUG=0
export WEB_CONCURRENCY=$(($(nproc) - 2 > 1 ? $(nproc) - 2 : 1))

rm -f /dev/shm/datastar-gpt-cmdqueue-*

sudo mkdir -p $DB_PATH
sudo chown -R $USER:$USER $DB_PATH
uv run schema/migrate.py

uv run python src/writer.py &
uv run uvicorn src.main:app --loop uvloop --host 0.0.0.0 --port 8000 &

wait