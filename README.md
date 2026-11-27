# TECHPRO

**Sistema de gestión para talleres de reparación y servicio técnico.**

TECHPRO centraliza clientes, órdenes de reparación, inventario, proveedores,
ventas y reportes con indicadores. El backend expone una API REST y el frontend
es una SPA con autenticación JWT en cookies HttpOnly.

## Stack

- **Frontend:** Angular 22, TypeScript y Tailwind CSS.
- **Backend:** Python, Django 5.2 y Django REST Framework.
- **Base de datos:** PostgreSQL 16 (SQLite solo para desarrollo y pruebas).
- **Autenticación:** SimpleJWT en cookies HttpOnly + protección CSRF.
- **Contenedores:** Docker Compose.

## Estructura

```text
TECHPRO/
├── client/                 # Angular SPA
│   └── src/app/            # login, dashboard, repairs, inventory, customers...
├── server/                 # Django + DRF
│   ├── accounts/           # Autenticación, roles y usuarios
│   ├── repairs/            # Órdenes de reparación
│   ├── workshop/           # Clientes, proveedores, inventario, ventas, reportes
│   ├── config/             # Settings, entorno y base de datos
│   ├── tests/              # Suite AUT-BE
│   └── .env.example        # Plantilla de variables (nunca subir .env)
├── testing/                # Plan, casos EF-01..EF-12 y suites AUT-API/E2E/ACC
├── tests/                  # Script de validación integral
├── docker-compose.yml
└── database.sql
```

## Requisitos

- Python 3.10 o superior.
- Node.js 18+ y npm.
- PostgreSQL 16 (o Docker).
- Docker y Docker Compose (opcional).

## Variables de entorno

Crear `server/.env` a partir de la plantilla:

```powershell
cd server
Copy-Item .env.example .env
```

Completar como mínimo:

| Variable | Uso | Ejemplo |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Clave de Django | Secreto aleatorio de 64+ caracteres |
| `JWT_SIGNING_KEY` | Firma de tokens JWT | Otro secreto aleatorio distinto |
| `DEBUG` | Modo desarrollo | `true` |
| `ENVIRONMENT` | Entorno | `development` |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Origen del frontend | `http://localhost:4200` |
| `CSRF_TRUSTED_ORIGINS` | Origen confiable CSRF | `http://localhost:4200` |
| `DB_ENGINE` | Motor | `postgresql` |
| `DB_NAME` | Base de datos | `techpro` |
| `DB_USER` | Usuario | `techpro` |
| `DB_PASSWORD` | Contraseña | Contraseña local |
| `DB_HOST` | Host | `127.0.0.1` |
| `DB_PORT` | Puerto | `5432` |
| `DB_SSLMODE` | SSL | `prefer` en local |
| `SQLITE_DB_NAME` | Solo pruebas | `test_local.sqlite3` |

Generar claves seguras:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

No commitear `server/.env`. El archivo está excluido por `.gitignore`.

## Base de datos y backend

### Opción A: Docker Compose

Desde la raíz, con `server/.env` configurado:

```powershell
docker compose up -d --build
```

API: [http://localhost:8000/api/](http://localhost:8000/api/)
Salud: [http://localhost:8000/api/health/](http://localhost:8000/api/health/)

### Opción B: local

Con PostgreSQL en ejecución y `server/.env` apuntando a `127.0.0.1`:

```powershell
cd server
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_test_users
python manage.py runserver 127.0.0.1:8000
```

Para pruebas rápidas sin PostgreSQL, en la misma terminal:

```powershell
$env:DEBUG = "true"
$env:ENVIRONMENT = "development"
$env:DB_ENGINE = "sqlite"
$env:SQLITE_DB_NAME = "test_local.sqlite3"
python manage.py migrate
```

## Frontend

```powershell
cd client
npm install
npm start
```

Frontend: [http://localhost:4200](http://localhost:4200)

## Usuarios de prueba por rol

El comando es idempotente y solo para desarrollo:

```powershell
cd server
python manage.py seed_test_users
```

| Rol | Email | Contraseña | Acceso |
| --- | --- | --- | --- |
| Administrador | `admin@techpro.local` | `TechproTest!2026` | Completo |
| Técnico | `tecnico@techpro.local` | `TechproTest!2026` | Completo |
| Vendedor | `vendedor@techpro.local` | `TechproTest!2026` | Completo |
| Consulta | `consulta@techpro.local` | `TechproTest!2026` | Solo lectura |

Cambiar la contraseña con `--password` o `TECHPRO_TEST_PASSWORD`. Con
`DEBUG=false` el comando exige `--force`.

## Suites de prueba

El índice completo está en [`testing/Testing.md`](testing/Testing.md).

### AUT-BE (Django + coverage)

```powershell
cd server
coverage run --branch manage.py test
coverage report -m
```

Cobertura esperada: ≥ 90 % de ramas. Configuración en `server/.coveragerc`.

### AUT-API (contrato HTTP)

Con el backend levantado y los usuarios creados:

```powershell
# En la terminal del servidor, para evitar 429 por el rate limit de login
$env:THROTTLE_RATE_LOGIN = "100/minute"
python manage.py runserver 127.0.0.1:8000

# En otra terminal, desde la raíz
python -m unittest discover -s testing/api -v
```

Variables: `TECHPRO_API_URL`, `TECHPRO_TEST_EMAIL`, `TECHPRO_TEST_PASSWORD`.

### AUT-E2E (Playwright)

Con backend y frontend levantados:

```powershell
cd testing/e2e
npm install
npx playwright install chromium
npm test
```

Variables: `TECHPRO_WEB_URL`, `TECHPRO_TEST_EMAIL`, `TECHPRO_TEST_PASSWORD`.

### ACC (aceptación manual)

Seguir el checklist [`testing/ACC.md`](testing/ACC.md) y registrar evidencias en
`testing/evidencias/`.

### Validación integral

```powershell
.\tests\run-validation.ps1
```

## Endpoints principales

### Autenticación (`/api/auth/`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/auth/csrf/` | Token CSRF para escrituras |
| `POST` | `/api/auth/register/` | Registro y cookies JWT |
| `POST` | `/api/auth/login/` | Login y cookies JWT |
| `POST` | `/api/auth/token/refresh/` | Rotación de tokens |
| `GET` | `/api/auth/me/` | Usuario autenticado |
| `POST` | `/api/auth/logout/` | Revocación y cierre de sesión |

### Recursos privados

| Recurso | Endpoints |
| --- | --- |
| Reparaciones | `/api/repairs/`, `/api/repairs/<id>/` |
| Clientes | `/api/customers/`, `/api/customers/<id>/` |
| Proveedores | `/api/suppliers/`, `/api/suppliers/<id>/` |
| Inventario | `/api/inventory/`, `/api/inventory/<id>/` |
| Ventas | `/api/sales/`, `/api/sales/<id>/` |
| Reportes | `/api/reports/summary/` |
| Salud | `/api/health/` |

Todos los recursos privados exigen autenticación y filtran los datos por
`created_by`. El rol `consulta` solo puede ejecutar `GET`, `HEAD` y `OPTIONS`.

---

**TECHPRO** — Gestión integral para talleres de reparación y servicio técnico.
