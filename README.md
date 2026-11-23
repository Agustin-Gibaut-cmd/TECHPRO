# TECHPRO

**Sistema de gestión para talleres de reparación y servicio técnico.**

## Descripción

TECHPRO es una aplicación web diseñada para centralizar y simplificar la gestión de talleres de reparación y servicio técnico. Permite administrar clientes, órdenes de reparación, inventario, proveedores, ventas y consultar reportes con indicadores y gráficos basados en los datos registrados.

## Tecnologías

- **Frontend:** Angular y TypeScript.
- **Backend:** Python, Django y Django REST Framework.
- **Base de datos:** PostgreSQL.
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
│       ├── reports/    # Reportes y estadísticas
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
├── endpoint.md         # Documentación de endpoints
└── README.md
```

## Requisitos

- Python 3.10 o superior.
- PostgreSQL.
- Node.js y npm.

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

Aplicar las migraciones e iniciar el servidor:

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Backend: http://127.0.0.1:8000/api/

### 3. Iniciar el frontend

Abrir una segunda terminal:

```powershell
cd client

npm install
npm start
```

Frontend: http://localhost:4200

---

**TECHPRO** — Gestión integral para talleres de reparación y servicio técnico.