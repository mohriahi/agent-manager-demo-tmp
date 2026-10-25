# The Cards Agent as Agent Manager builds it from this repository, with the
# agents/ folder as its build context. Agent Manager adds its tracing when it
# deploys it, so the image carries none.
FROM python:3.11-slim
WORKDIR /app
# Agent Manager runs agents on a read-only disk: nothing is written but to /tmp.
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/tmp LITELLM_LOCAL_MODEL_COST_MAP=True \
    ANTHROPIC_OPEN_TELEMETRY=false
COPY cards-agent/requirements.txt .
# A compiler for the few packages without a ready-made build on this machine's chip.
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
 && pip install --no-cache-dir --root-user-action=ignore -r requirements.txt \
 && apt-get purge -y gcc libc6-dev && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
COPY common ./common
COPY cards-agent/ .
# Agent Manager runs only images that do not run as root.
USER 10001
CMD ["python", "main.py"]
