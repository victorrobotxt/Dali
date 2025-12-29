#!/bin/bash
# Optimized Scans the repo and dumps text files for LLM context

output="glashaus_context.txt"
echo "--- GLASHAUS PROJECT DUMP ---" > "$output"
date >> "$output"

echo -e "\n\n--- GIT HISTORY ---" >> "$output"
git log --oneline --graph --decorate -n 20 >> "$output"

echo -e "\n\n--- FILE STRUCTURE ---" >> "$output"
# Expanded exclusion list for the tree view
tree -L 3 -I '.git|__pycache__|*.pyc|storage|archive|*.png|*.jpg' >> "$output" 2>/dev/null

echo -e "\n\n--- FILE CONTENTS ---" >> "$output"
find . -type f \
    -not -path '*/.*' \
    -not -path '*/__pycache__*' \
    -not -path './storage/*' \
    -not -path './forensics/*.html' \
    -not -name '*.pyc' \
    -not -name 'cookies.txt' \
    -not -name '*.sqlite' \
    -not -name '*.png' \
    -not -name '*.jpg' \
    -not -name 'glashaus_context.txt' \
    -not -path './scraper_service.py' \
    -not -path './manual_session_audit.py' \
    | while read -r file; do
    
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
