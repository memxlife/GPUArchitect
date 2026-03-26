#!/bin/bash

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set"
    exit 1
fi

python main.py --benchmark memory --llm-analysis
