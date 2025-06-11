#!/bin/sh
set -e

if [ ! -f /app/index/index.json ]; then
    echo "[entrypoint] Index not found, building index..."
    python /app/main.py --reindex
else
    echo "[entrypoint] Index found, skipping rebuild."
fi

exec supervisord -c /app/supervisord.conf 