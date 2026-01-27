#!/bin/bash

# --- CONFIGURATION ---
# Since API isn't exposed directly, we skip localhost:8000 and test via Nginx
NGINX_URL="http://localhost:8080" 

CONTAINER_API="dali-api-1"
CONTAINER_WORKER="dali-worker-1"

# Internal Docker Service Names (Service names in docker-compose.yml)
INTERNAL_DB_HOST="db"       
INTERNAL_REDIS_HOST="redis" 

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}>>> Starting Deep Health Check for Dali Stack...${NC}\n"

# ---------------------------------------------------------
# 1. NGINX REVERSE PROXY (The Main Entrypoint)
# ---------------------------------------------------------
echo -e "1. Testing Nginx Proxy (External access on Port 8080)..."

# We verify that Nginx can talk to the API by hitting the docs endpoint
HTTP_CODE_NGINX=$(curl -s -o /dev/null -w "%{http_code}" "$NGINX_URL/docs")

if [ "$HTTP_CODE_NGINX" == "200" ]; then
    echo -e "   [${GREEN}OK${NC}] Nginx (Port 8080) -> API Docs is reachable."
else
    echo -e "   [${RED}FAIL${NC}] Nginx check failed (HTTP $HTTP_CODE_NGINX)."
    echo "         Ensure 'dali-nginx-1' is running and mapped to 8080."
fi

# ---------------------------------------------------------
# 2. INTERNAL CONNECTIVITY
# ---------------------------------------------------------
echo -e "\n2. Testing Internal Network (From inside $CONTAINER_API)..."

# Test Connection to Postgres
# Using 'nc' (netcat) assuming it was installed in the Dockerfile
if docker exec $CONTAINER_API nc -z -v $INTERNAL_DB_HOST 5432 2>&1 | grep -q "open"; then
    echo -e "   [${GREEN}OK${NC}] API -> Postgres ($INTERNAL_DB_HOST:5432) is OPEN"
else
    # Fallback Python check
    echo -e "   [${YELLOW}RETRY${NC}] 'nc' failed/missing. Trying Python..."
    if docker exec $CONTAINER_API python -c "import socket; s=socket.socket(); s.connect(('$INTERNAL_DB_HOST', 5432)); print('ok')" > /dev/null 2>&1; then
        echo -e "   [${GREEN}OK${NC}] API -> Postgres ($INTERNAL_DB_HOST:5432) is OPEN (Verified via Python)"
    else
        echo -e "   [${RED}FAIL${NC}] API cannot reach Postgres."
    fi
fi

# Test Connection to Redis
if docker exec $CONTAINER_API nc -z -v $INTERNAL_REDIS_HOST 6379 2>&1 | grep -q "open"; then
    echo -e "   [${GREEN}OK${NC}] API -> Redis ($INTERNAL_REDIS_HOST:6379) is OPEN"
else
    echo -e "   [${YELLOW}RETRY${NC}] 'nc' failed/missing. Trying Python..."
    if docker exec $CONTAINER_API python -c "import socket; s=socket.socket(); s.connect(('$INTERNAL_REDIS_HOST', 6379)); print('ok')" > /dev/null 2>&1; then
        echo -e "   [${GREEN}OK${NC}] API -> Redis ($INTERNAL_REDIS_HOST:6379) is OPEN (Verified via Python)"
    else
        echo -e "   [${RED}FAIL${NC}] API cannot reach Redis."
    fi
fi

# ---------------------------------------------------------
# 3. CELERY WORKER BEHAVIOR
# ---------------------------------------------------------
echo -e "\n3. Testing Celery Worker Task Execution..."

TEST_ID="TEST_PING_$(date +%s)"

echo -e "   -> Injecting task: $TEST_ID"

# Inject task via Python shell inside the API container
docker exec $CONTAINER_API python -c "
from src.worker import celery_app
try:
    # Attempt to send task
    res = celery_app.send_task('src.tasks.audit_listing', args=['$TEST_ID'])
    print(f'Task Sent with ID: {res.id}')
except Exception as e:
    print(f'Error sending task: {e}')
" > /dev/null 2>&1

# Wait for worker to process
sleep 3

# Check logs
if docker logs $CONTAINER_WORKER 2>&1 | grep -q "$TEST_ID"; then
    echo -e "   [${GREEN}OK${NC}] Worker processed task payload: $TEST_ID"
else
    echo -e "   [${YELLOW}CHECK${NC}] Worker logs did not show the ID '$TEST_ID'."
    echo "         Run 'docker-compose logs worker' to see if the task failed."
fi

echo -e "\n${YELLOW}>>> Test Complete.${NC}"
