FROM python:3.9-slim

WORKDIR /app

# Install package
COPY pyproject.toml .
COPY src/ /app/src/
COPY config.yaml .
RUN pip install --no-cache-dir .

# Create directories
RUN mkdir -p /app/data /app/logs

# Volume for persistence
VOLUME ["/app/data", "/app/logs"]

# Default command: Run Scheduler (every 24 hours)
CMD ["optoagent-scheduler", "--interval", "24"]
