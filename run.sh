#!/usr/bin/env bash
# Starts the Agent Manager demo next to the main demo: sets Agent Manager up
# for the bank (setup.py), then starts the agents and the page.
#
# Needs the main demo running (./scripts/run-local.sh) and Agent Manager
# installed and running (its quick start).
set -euo pipefail
cd "$(dirname "$0")"

python3 setup.py
docker compose --env-file config.env --env-file secrets.env up -d --build --remove-orphans

port="$(sed -n 's/^PAGE_PORT=//p' config.env)"
# Ready once the page answers with the Cards Agent's version: the agents are up.
for _ in $(seq 1 60); do
  curl -sf "http://localhost:$port/api/config" | grep -q '"release": "v' && break
  sleep 1
done
echo
echo "Agent Manager demo: http://localhost:$port"
