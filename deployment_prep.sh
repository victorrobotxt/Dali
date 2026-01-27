#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

echo ">>> [GLASHAUS] INITIATING DEPLOYMENT PREPARATION PROTOCOL..."

# ==========================================
# 1. CLEANUP PHASE
# ==========================================
echo "[*] Removing demo files and temporary artifacts..."

# Remove the HTML demo as requested
rm -f index.html

# Remove the context dump itself if present (don't ship the map with the territory)
rm -f glashaus_context.txt

# Remove sensitive local data or temp files
rm -f cookies.txt
rm -f bypass_audit.py # Moving logic to scripts/poc instead of deleting, see below
rm -f manual_session_audit.py # Moving logic to scripts/poc
rm -f test_forensics.py # Moving to scripts
rm -rf __pycache__
rm -rf */__pycache__
rm -rf */*/__pycache__

# ==========================================
# 2. STRUCTURAL REORGANIZATION
# ==========================================
echo "[*] Standardizing directory structure..."

# Create standard directories if they don't exist
mkdir -p storage/laws
mkdir -p storage/archive
mkdir -p resources/headers
mkdir -p resources/prompts
mkdir -p scripts/poc
mkdir -p logs

# --- Move Root Scripts to scripts/ directory ---
# These are manual tools, not part of the core app source
if [ -f "bypass_audit.py" ]; then mv bypass_audit.py scripts/poc/bypass_audit_poc.py; fi
if [ -f "manual_session_audit.py" ]; then mv manual_session_audit.py scripts/poc/session_audit_poc.py; fi
if [ -f "test_forensics.py" ]; then mv test_forensics.py scripts/manual_forensics_check.py; fi

# --- Move Resources ---
# Move raw text files and prompts out of root/top-level folders into a clean resources folder
if [ -f "law.txt" ]; then mv law.txt storage/laws/raw_law_dump.txt; fi
if [ -d "forensics" ]; then 
    mv forensics/headers.txt resources/headers/chrome_headers.txt 2>/dev/null || true
    rmdir forensics 2>/dev/null || true
fi
if [ -d "prompts" ]; then
    mv prompts/*.md resources/prompts/ 2>/dev/null || true
    rmdir prompts 2>/dev/null || true
fi

# ==========================================
# 3. DEPLOYMENT CONFIGURATION
# ==========================================
echo "[*] Generating deployment configurations..."

# Create .dockerignore to prevent local virtualenvs/git from blooming the build context
cat > .dockerignore <<EOF
.git
.gitignore
.env
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
storage/
logs/
glashaus_context.txt
deployment_prep.sh
EOF

# Create a production-ready .env.example (Safe to commit)
cat > .env.example <<EOF
# --- GLASHAUS CONFIGURATION ---

# DATABASE
POSTGRES_USER=glashaus_user
POSTGRES_PASSWORD=change_me_in_prod
POSTGRES_DB=glashaus_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

# INFRASTRUCTURE
REDIS_URL=redis://redis:6379/0
SECRET_KEY=generate_a_secure_random_string_here

# EXTERNAL APIS
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash
GOOGLE_MAPS_API_KEY=your_maps_key_optional
EOF

# ==========================================
# 4. PERMISSIONS & FINAL CHECKS
# ==========================================
echo "[*] Setting permissions..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true

echo ">>> [GLASHAUS] REORGANIZATION COMPLETE."
echo ">>> PROJECT READY FOR DEPLOYMENT."
echo ">>> NEXT STEPS:"
echo "    1. cp .env.example .env (and fill in secrets)"
echo "    2. docker-compose up --build"