#!/bin/bash
# Lancer Astyria sur macOS / Linux
cd "$(dirname "$0")"
PORT=${1:-8000}
python3 server.py $PORT
