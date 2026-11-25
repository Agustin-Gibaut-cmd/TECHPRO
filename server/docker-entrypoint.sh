#!/bin/sh
set -eu

# Entrypoint del contenedor backend de Django (TECHPRO):
# 1. Espera a que PostgreSQL acepte conexiones usando las variables de entorno DB_*.
# 2. Aplica las migraciones pendientes de Django sin intervención interactiva.
# 3. Inicia el servidor de desarrollo en 0.0.0.0:8000 reemplazando el proceso shell (exec).

MAX_RETRIES=30
RETRY_INTERVAL=2

can_connect_db() {
  python - <<'PY'
import os
import sys
import psycopg

try:
    with psycopg.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ.get("DB_PASSWORD", ""),
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        sslmode=os.environ.get("DB_SSLMODE") or "disable",
        connect_timeout=3,
    ):
        pass
except Exception as exc:
    print(exc, file=sys.stderr)
    sys.exit(1)
PY
}

wait_for_db() {
  echo "Esperando a PostgreSQL en ${DB_HOST}:${DB_PORT}..."
  attempt=0

  while [ "$attempt" -lt "$MAX_RETRIES" ]; do
    if can_connect_db; then
      return 0
    fi

    attempt=$((attempt + 1))
    sleep "$RETRY_INTERVAL"
  done

  echo "PostgreSQL no aceptó la conexión." >&2
  exit 1
}

wait_for_db
python manage.py migrate --noinput
exec python manage.py runserver 0.0.0.0:8000 --noreload