# One image recipe for every agent: its own framework, the shared code, and
# Agent Manager's instrumentation, which traces it without code changes.
FROM python:3.12-slim
ARG AGENT
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY ${AGENT}/requirements.txt .
# A compiler for the few packages without a ready-made build on this machine's chip.
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
 && pip install --no-cache-dir --root-user-action=ignore -r requirements.txt amp-instrumentation==0.4.2 \
 && apt-get purge -y gcc libc6-dev && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
# Each model call is traced once, by the framework's instrumentation.
ENV ANTHROPIC_OPEN_TELEMETRY=false
COPY common ./common
COPY ${AGENT}/ .
CMD ["amp-instrument", "python", "main.py"]
