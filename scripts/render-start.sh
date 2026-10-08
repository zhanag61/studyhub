#!/usr/bin/env bash
set -euo pipefail

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers 2 --threads 2 --timeout 60 \
  --access-logfile - --error-logfile -
