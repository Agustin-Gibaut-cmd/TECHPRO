# Docker — backend Django y PostgreSQL

Django y PostgreSQL corren en la misma red de Docker. El backend no usa el PostgreSQL de Windows: esa conexión se cortaba (`host.docker.internal`) y el contenedor se apagaba y volvía a arrancar.

| Archivo | Rol |
|---|---|
| `docker-compose.yml` | Servicios `db` y `backend` |
| `server/Dockerfile` | Imagen de Django |
| `server/docker-entrypoint.sh` | Espera la base, migra y deja `runserver` en `0.0.0.0:8000` |
| `server/.env` | Nombre, usuario y contraseña de la base. Compose los inyecta a los dos servicios |

`DB_HOST`, `DB_PORT` y `DB_SSLMODE` del contenedor los fija `docker-compose.yml` (`db`, `5432`, `disable`). El Postgres de la imagen no usa TLS. Con `DEBUG=True` eso es válido.

## Requisitos

- Docker Desktop en ejecución.
- `server/.env` con `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DJANGO_SECRET_KEY`, `JWT_SIGNING_KEY`, `DEBUG=True` y `ENVIRONMENT=development`.

## Levantar

Desde la raíz del repositorio:

```powershell
docker compose up -d --build
```

- API: http://localhost:8000/api/
- Salud: http://localhost:8000/api/health/

La base queda en el volumen `postgres_data`. No publica el puerto `5432`, así no choca con un PostgreSQL local.

```powershell
docker compose ps
docker compose logs -f backend
```

## Detener

```powershell
docker compose stop
```

`docker compose start` lo vuelve a dejar en segundo plano. `docker compose down` borra los contenedores y conserva el volumen. `docker compose down -v` borra también los datos.

## Si se reinicia

```powershell
docker compose logs --tail 80 backend
docker compose logs --tail 80 db
```

Después de cambiar `server/.env`:

```powershell
docker compose up -d --force-recreate
```

`ENVIRONMENT=production` con `DEBUG=True` hace que Django cierre el proceso. Dejalos en `development` y `True` para este entorno.

Si el log dice `relation "auth_user" already exists`, el volumen tiene tablas viejas y Django no las tiene registradas. Con la base vacía, esto la deja nueva y vuelve a migrar:

```powershell
docker compose down -v
docker compose up -d --build
```
