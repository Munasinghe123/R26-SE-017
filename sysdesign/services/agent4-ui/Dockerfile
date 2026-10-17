FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy packages and dependencies
COPY packages/ /app/packages/
COPY services/agent4-ui/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir -e /app/packages/contracts -e /app/packages/shared

# Copy service code
COPY services/agent4-ui/ /app/services/agent4-ui/

WORKDIR /app/services/agent4-ui

EXPOSE 8004

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8004"]
