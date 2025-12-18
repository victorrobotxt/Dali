#!/bin/bash
# Scans the repo and dumps text files for LLM context
output="glashaus_context.txt"
echo "--- GLASHAUS PROJECT DUMP ---" > "$output"
date >> "$output"
echo "Structure:" >> "$output"
tree -L 3 -I '.git' >> "$output" 2>/dev/null || find . -maxdepth 3 -not -path '*/.*' >> "$output"

echo -e "\n\n--- FILE CONTENTS ---" >> "$output"
find . -type f \
    -not -path '*/.*' \
    -not -path './glashaus_context.txt' \
    -not -name '*.png' \
    -not -name '*.jpg' \
    | while read -r file; do
    echo -e "\n\n=========================================" >> "$output"
    echo "FILE: $file" >> "$output"
    echo "=========================================" >> "$output"
    cat "$file" >> "$output"
done

echo "Dump complete. Copy contents of $output"
