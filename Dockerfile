# Use Official Python Runtime
FROM python:3.11-slim

# Set Working Directory
WORKDIR /app

# Install System Dependencies (Postgres + GIS libs)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Code
COPY . .

# Expose Port
EXPOSE 8000

# Start Command (Wait for DB, then launch)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
