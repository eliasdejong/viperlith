#!/bin/bash

export DEBUG="0"

uv run uvicorn src.main:app --loop uvloop --env-file .env --host 0.0.0.0 --port 8000