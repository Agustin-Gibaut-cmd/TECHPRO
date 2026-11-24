## Comandos clave (siempre desde la raíz del proyecto)

- **Levantar y construir:** `docker compose up -d --build` (API en `http://localhost:8000/api/` y salud en `http://localhost:8000/api/health/`).
- **Ver estado y logs:** `docker compose ps` y `docker compose logs -f backend`.
- **Pausar y reanudar:** `docker compose stop` para detener; `docker compose start` para volver a arrancar.
- **Bajar conservando la base:** `docker compose down` (mantiene el volumen `postgres_data`).
- **Aplicar cambios de `server/.env`:** `docker compose up -d --force-recreate` (mantener `ENVIRONMENT=development` y `DEBUG=True`).
- **Reiniciar la base desde cero:** `docker compose down -v` y luego `docker compose up -d --build` (borra los datos del volumen; útil si aparece `relation "auth_user" already exists`).

## Usuarios en Django (desde la raíz del proyecto)

Recordá usar el **mismo correo** en `username` y `email` (en minúsculas) para que coincida con el flujo de login de `TECHPRO`:

- **Crear superusuario:** `docker compose exec backend python manage.py createsuperuser`
- **Crear usuario normal desde consola:**
  ```powershell
  docker compose exec backend python manage.py shell -c "from django.contrib.auth import get_user_model; U = get_user_model(); U.objects.create_user(username='usuario@techpro.local', email='usuario@techpro.local', first_name='Nombre', password='ClaveSegura1234!')"