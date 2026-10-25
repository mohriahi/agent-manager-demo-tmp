# The Travel Desk as Agent Manager builds it from this repository, with the
# agents/ folder as its build context. Agent Manager adds its tracing when it
# deploys it, so the image carries none.
FROM python:3.11-slim
WORKDIR /app
# Agent Manager runs agents on a read-only disk: nothing is written but to /tmp.
# CrewAI's own telemetry is off; Agent Manager's tracing stays on.
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/tmp ANTHROPIC_OPEN_TELEMETRY=false \
    CREWAI_DISABLE_TELEMETRY=true CREWAI_TRACING_ENABLED=false
COPY travel-desk/requirements.txt .
# A compiler for the few packages without a ready-made build on this machine's chip.
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
 && pip install --no-cache-dir --root-user-action=ignore -r requirements.txt \
 && apt-get purge -y gcc libc6-dev && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
COPY common ./common
COPY travel-desk/ .
# Agent Manager runs only images that do not run as root.
USER 10001
CMD ["python", "main.py"]
