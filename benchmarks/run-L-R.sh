#!/bin/bash

set -a; source .env.bench-large; set +a

export WRK_READ_PCT=100

wrk -t4 -c1k -d60s -s common.lua --latency http://127.0.0.1:8000

