#!/bin/bash

set -a; source .env; set +a

export DEBUG="${DEBUG:-1}"
export PYTHONPATH=.

uv run src/main.py