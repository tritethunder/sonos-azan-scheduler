FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY azan_scheduler.py .
COPY web_control.py .
COPY control_azan.py .
COPY config.json .

# Default command (can be overridden)
CMD ["python", "azan_scheduler.py"]
