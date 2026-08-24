#!/bin/bash

set -a; source ../.env; set +a
set -a; source .env.bench-large; set +a


export PYTHONPATH=../.

uv run seed_common.py