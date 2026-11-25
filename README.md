# TECHPRO

**Sistema de gestión para talleres de reparación y servicio técnico.**

## Descripción

TECHPRO es una aplicación web diseñada para centralizar y simplificar la gestión de talleres de reparación y servicio técnico. Permite administrar clientes, órdenes de reparación, inventario, proveedores, ventas y consultar reportes con indicadores y gráficos basados en los datos registrados.

## Tecnologías

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,django,docker,postgres,angular,ts,tailwind&theme=dark" alt="Tecnologías utilizadas en TECHPRO">
</p>

- **Frontend:** Angular y TypeScript.
- **Estilos:** Tailwind CSS.
- **Backend:** Python, Django y Django REST Framework.
- **Base de datos:** PostgreSQL.
- **Contenedores:** Docker.
- **Autenticación:** JWT mediante cookies HttpOnly.

## Estructura del repositorio

```text
TECHPRO/
│
├── client/
│   └── src/app/
│       ├── auth-form/   # Acceso y registro
│       ├── customers/   # Clientes
│       ├── dashboard/  # Panel principal
│       ├── inventory/  # Inventario
│       ├── login/      # Inicio de sesión
│       ├── repairs/    # Reparaciones
│       ├── reports/   # Reportes y estadísticas
│       ├── sales/      # Ventas
│       └── suppliers/  # Proveedores
│
├── server/
│   ├── accounts/       # Autenticación y usuarios
│   ├── repairs/        # API de reparaciones
│   ├── workshop/       # Módulos de gestión
│   ├── config/         # Configuración de Django
│   ├── tests/          # Pruebas del backend
│   └── requirements.txt
│
├── tests/              # Validaciones generales
├── database.sql        # Referencia de tablas
├── image.png           # Logo de presentación
└── README.md
```

## Requisitos

- Python 3.10 o superior.
- PostgreSQL.
- Node.js y npm.
- Docker y Docker Compose (opcional).

## Cómo levantar el proyecto

### 1. Clonar el repositorio

```bash
git clone URL_DEL_REPOSITORIO
cd TECHPRO
```

### 2. Iniciar el backend

Desde una terminal:

```powershell
cd server

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

Copy-Item .env.example .env
```

Configurar las variables de entorno y las credenciales de PostgreSQL en `server/.env`.

Generar dos claves secretas diferentes:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Configurar una en `DJANGO_SECRET_KEY` y otra en `JWT_SIGNING_KEY`.

En `server/.env`, para este arranque local usá `DB_HOST=127.0.0.1` y `DB_SSLMODE=prefer`.

Aplicar las migraciones e iniciar el servidor:

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Backend: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

Con Docker, desde la raíz del repositorio, el backend y PostgreSQL quedan en segundo plano:

```powershell
docker compose up -d --build
```

API: [http://localhost:8000/api/](http://localhost:8000/api/)

El detalle está en `docker.md`.

### 3. Iniciar el frontend

Abrir una segunda terminal:

```powershell
cd client

npm install
npm start
```

Frontend: [http://localhost:4200](http://localhost:4200)

## Endpoints de la API

### Autenticación (`/api/auth/`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/auth/csrf/` | Obtiene el token CSRF para solicitudes de escritura. |
| `POST` | `/api/auth/register/` | Registra una cuenta nueva y emite cookies JWT HttpOnly. |
| `POST` | `/api/auth/login/` | Inicia sesión y emite cookies JWT HttpOnly. |
| `POST` | `/api/auth/token/refresh/` | Renueva y rota los tokens JWT sin exponerlos en el body. |
| `GET` | `/api/auth/me/` | Obtiene los datos de la cuenta actualmente autenticada. |
| `POST` | `/api/auth/logout/` | Revoca la sesión y elimina las cookies HttpOnly. |

### Reparaciones (`/api/repairs/`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/repairs/` | Lista las órdenes de reparación del usuario actual. |
| `POST` | `/api/repairs/` | Registra una nueva orden de reparación. |
| `PUT`, `PATCH` | `/api/repairs/<id>/` | Actualiza los datos o el estado de una reparación existente. |

### Clientes (`/api/customers/`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/customers/` | Lista los clientes registrados por el usuario. |
| `POST` | `/api/customers/` | Registra un nuevo cliente. |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/customers/<id>/` | Consulta, edita o elimina un cliente específico. |

### Inventario (`/api/inventory/`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/inventory/` | Lista todos los productos y repuestos en inventario. |
| `POST` | `/api/inventory/` | Agrega un nuevo producto o repuesto al inventario. |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/inventory/<id>/` | Consulta, edita o elimina un producto de inventario. |

### Proveedores (`/api/suppliers/`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/suppliers/` | Lista los proveedores registrados por el usuario. |
| `POST` | `/api/suppliers/` | Registra un nuevo proveedor. |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/suppliers/<id>/` | Consulta, edita o elimina un proveedor. |

### Ventas (`/api/sales/`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/sales/` | Lista las ventas registradas ordenadas cronológicamente. |
| `POST` | `/api/sales/` | Registra una nueva venta de producto. |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/sales/<id>/` | Consulta, modifica o elimina un registro de venta. |

### Reportes (`/api/reports/`)

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/reports/summary/` | Retorna estadísticas consolidadas e indicadores para los gráficos del dashboard (ventas mensuales, productos destacados, stock bajo y reparaciones). |

### Salud del sistema

| Método | Endpoint | Descripción |
| --- | --- | --- |
| `GET` | `/api/health/` | Comprueba el estado y disponibilidad del servicio backend. |

---

**TECHPRO** — Gestión integral para talleres de reparación y servicio técnico.
