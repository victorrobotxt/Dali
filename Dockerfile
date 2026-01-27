# STAGE 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
RUN apt-get update && apt-get install -y \
    libpq-dev gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# STAGE 2: Runtime
FROM python:3.11-slim as runtime

WORKDIR /app

# Install runtime libs
RUN apt-get update && apt-get install -y \
    libpq5 netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create user FIRST
RUN useradd -m glashaus_user

# Copy dependencies to the USER'S home, not root's
COPY --from=builder /root/.local /home/glashaus_user/.local

# Ensure the user owns their own dependencies
RUN chown -R glashaus_user:glashaus_user /home/glashaus_user/.local

# Update PATH to point to the user's local bin
ENV PATH=/home/glashaus_user/.local/bin:$PATH

# Copy App Code with correct ownership
COPY --chown=glashaus_user:glashaus_user . .

RUN mkdir -p storage/archive && chown -R glashaus_user:glashaus_user /app

USER glashaus_user

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
