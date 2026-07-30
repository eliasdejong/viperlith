#!/bin/bash

set -a; source .env; set +a

export DEBUG="${DEBUG:-1}"

uv run schema/migrate.py

if [ "$DEBUG" -eq 1 ]; then
	uv run uvicorn src.main:app --loop uvloop --reload --log-level debug
else
	uv run uvicorn src.main:app --loop uvloop --host 0.0.0.0 --port 8000
fi