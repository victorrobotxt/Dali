#!/bin/bash
# Scans the repo and dumps text files for LLM context
output="glashaus_context.txt"
echo "--- GLASHAUS PROJECT DUMP ---" > "$output"
date >> "$output"

echo -e "\n\n--- GIT HISTORY ---" >> "$output"
git log --oneline --graph --decorate -n 20 >> "$output"

echo -e "\n\n--- FILE STRUCTURE ---" >> "$output"
tree -L 3 -I '.git|__pycache__|*.pyc' >> "$output" 2>/dev/null || find . -maxdepth 3 -not -path '*/.*' >> "$output"

echo -e "\n\n--- FILE CONTENTS ---" >> "$output"
find . -type f \
    -not -path '*/.*' \
    -not -path './glashaus_context.txt' \
    -not -name '*.png' \
    -not -name '*.jpg' \
    -not -name '*.sqlite' \
    | while read -r file; do
    echo -e "\n\n=========================================" >> "$output"
    echo "FILE: $file" >> "$output"
    echo "=========================================" >> "$output"
    cat "$file" >> "$output"
done

echo "Dump complete. Copy contents of $output"
