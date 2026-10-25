#!/usr/bin/env bash
# Starts the Agent Manager demo: sets Agent Manager up for the bank
# (configure/: the agents it builds and runs, their rules and checks), then
# starts the two agents that run outside it, and the page.
#
# Needs Agent Manager installed and running (its quick start), this
# repository on GitHub, and an Anthropic key in the file config.env points to.
set -euo pipefail
cd "$(dirname "$0")"

python3 -m configure
docker compose --env-file config.env --env-file secrets.env up -d --build --remove-orphans

port="$(sed -n 's/^PAGE_PORT=//p' config.env)"
# Ready once the page answers with what Agent Manager runs where.
for _ in $(seq 1 90); do
  curl -sf "http://localhost:$port/api/control" | grep -q '"production"' && break
  sleep 1
done
echo
echo "Agent Manager demo: http://localhost:$port"
