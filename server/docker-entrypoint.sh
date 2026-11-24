#!/bin/sh
set -eu

echo "Esperando a PostgreSQL en ${DB_HOST}:${DB_PORT}..."
attempt=0
until python - <<'PY'
import os
import sys

import psycopg

try:
    connection = psycopg.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ.get("DB_PASSWORD", ""),
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        sslmode=os.environ.get("DB_SSLMODE") or "disable",
        connect_timeout=3,
    )
except Exception as exc:
    print(exc, file=sys.stderr)
    sys.exit(1)
else:
    connection.close()
PY
do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    echo "PostgreSQL no aceptó la conexión."
    exit 1
  fi
  sleep 2
done

python manage.py migrate --noinput
exec python manage.py runserver 0.0.0.0:8000 --noreload
