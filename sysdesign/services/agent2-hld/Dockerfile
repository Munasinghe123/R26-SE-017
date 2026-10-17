FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy packages and service dependencies
COPY packages/ /app/packages/
COPY services/agent2-hld/requirements.txt /app/requirements.txt

# Install PyTorch CPU first to avoid heavy GPU/CUDA wheels, then rest of requirements
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir -e /app/packages/contracts -e /app/packages/shared

# Copy service code
COPY services/agent2-hld/ /app/services/agent2-hld/

WORKDIR /app/services/agent2-hld

EXPOSE 8002

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8002"]
