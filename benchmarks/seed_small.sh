#!/bin/bash

set -a; source ../.env; set +a
set -a; source .env.bench-small; set +a


export PYTHONPATH=../.

uv run seed_common.py