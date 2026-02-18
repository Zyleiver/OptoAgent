FROM python:3.9-slim

WORKDIR /app

# Install dependencies
# We don't have a requirements.txt yet, so we install directly or create one.
# Valid structure: COPY requirements.txt . -> RUN pip install...
# For now, inline install implementation:
RUN pip install requests schedule

# Copy source code
COPY src/ /app/src/

# Create data directory
RUN mkdir -p /app/data

# Volume for persistence
VOLUME /app/data

# Default command: Run Scheduler
CMD ["python", "src/scheduler.py", "--interval", "24"]
