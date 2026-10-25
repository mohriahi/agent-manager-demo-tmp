#!/usr/bin/env bash
# Starts the Agent Manager demo: sets Agent Manager up for the bank
# (configure/), then starts the agents, Core Banking and the page.
#
# Needs Agent Manager installed and running (its quick start), and an
# Anthropic key in the file config.env points to.
set -euo pipefail
cd "$(dirname "$0")"

python3 -m configure
docker compose --env-file config.env --env-file secrets.env up -d --build --remove-orphans

port="$(sed -n 's/^PAGE_PORT=//p' config.env)"
# Ready once the page answers with the Cards Agent's version: the agents are up.
for _ in $(seq 1 90); do
  curl -sf "http://localhost:$port/api/config" | grep -q '"release": "v' && break
  sleep 1
done
echo
echo "Agent Manager demo: http://localhost:$port"
