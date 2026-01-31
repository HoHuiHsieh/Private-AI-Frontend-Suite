#!/bin/bash
# Use hypercorn for multi-worker, pooling, and auto-reload (Linux)
export PYTHONPATH=$(pwd)/src
hypercorn src.main:app --bind 0.0.0.0:3000 --workers 8 --worker-class asyncio --reload
