#!/bin/bash
# Optimized Scans the repo and dumps text files for LLM context

output="glashaus_context.txt"
echo "--- GLASHAUS PROJECT DUMP ---" > "$output"
date >> "$output"

# Define directories to completely ignore (folders)
IGNORE_DIRS="(node_modules|.next|.git|__pycache__|storage|logs|archive|.venv|venv|dist|build)"

# Define specific file names/extensions to ignore
IGNORE_FILES="(*.pyc|*.png|*.ico|*.jpg|*.svg|*.sqlite|*.lock|package-lock.json|bun.lockb|yarn.lock|.DS_Store)"

echo -e "\n\n--- GIT HISTORY ---" >> "$output"
git log --oneline --graph --decorate -n 20 >> "$output"

echo -e "\n\n--- FILE STRUCTURE ---" >> "$output"
# Uses the ignore pattern for tree
tree -L 3 -I "$IGNORE_DIRS|$IGNORE_FILES" >> "$output" 2>/dev/null

echo -e "\n\n--- FILE CONTENTS ---" >> "$output"

# The logic below uses -prune to skip entire directory trees efficiently
find . \
    -type d -regextype posix-extended -regex ".*/$IGNORE_DIRS" -prune -o \
    -type f \
    -not -name 'glashaus_context.txt' \
    -not -name '*.pyc' \
    -not -name '*.png' \
    -not -name '*.jpg' \
    -not -name '*.svg' \
    -not -name '*.sqlite' \
    -not -name 'package-lock.json' \
    -not -path './scraper_service.py' \
    -not -path './manual_session_audit.py' \
    -print | while read -r file; do
    
    # Skip files larger than 50KB (likely raw data dumps/logs)
    # except for the main schema or specific logic files
    filesize=$(wc -c <"$file")
    if [ $filesize -gt 50000 ] && [[ "$file" != *"schema"* ]]; then
        echo -e "\n\n[SKIPPING $file - TOO LARGE: $filesize bytes]" >> "$output"
        continue
    fi

    echo -e "\n\n=========================================" >> "$output"
    echo "FILE: $file" >> "$output"
    echo "=========================================" >> "$output"
    cat "$file" >> "$output"
done

echo "Dump complete. Size: $(du -h $output | cut -f1)"
