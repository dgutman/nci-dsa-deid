#!/bin/bash

output=""

for file in *.py; do
    # Ensure that we're only adding actual files and not directories
    if [ -f "$file" ]; then
        output+="\n\n---- $file ----\n\n"
        output+=$(cat "$file")
    fi
done

echo -e "$output" | pbcopy
