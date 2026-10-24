# Runs the agent outside Agent Manager, as an externally hosted agent:
# amp-instrumentation sends its traces to Agent Manager.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt amp-instrumentation==0.4.2
COPY main.py .
CMD ["amp-instrument", "python", "main.py"]
