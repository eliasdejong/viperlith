#!/bin/bash

export DEBUG="1"

uv run uvicorn src.main:app --loop uvloop --env-file .env --reload --log-level debug