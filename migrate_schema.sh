#!/bin/bash

set -a; source .env; set +a

sudo mkdir -p $DB_PATH
sudo chown -R $USER:$USER $DB_PATH

uv run schema/migrate.py