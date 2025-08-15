#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}

echo "fastapi run on $HOST:$PORT with $WORKERS workers"
exec uvicorn app:app --host "$HOST" --port "$PORT" --workers "$WORKERS"
