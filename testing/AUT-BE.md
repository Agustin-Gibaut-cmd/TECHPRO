# AUT-BE — Pruebas automatizadas de backend

## Requisitos

- Python 3.10+ y dependencias de `server/requirements.txt`.
- `coverage` incluido en `requirements.txt`.
- Base temporal de Django. Para evitar depender de PostgreSQL:

```powershell
cd server
$env:DEBUG = "true"
$env:ENVIRONMENT = "development"
$env:DB_ENGINE = "sqlite"
$env:SQLITE_DB_NAME = "test_local.sqlite3"
```

## Comando principal

```powershell
cd server
coverage run --branch manage.py test
coverage report -m
```

El resultado esperado es `OK` y una cobertura de ramas superior a 90 %.

## Ejecución por módulo

```powershell
python manage.py test tests.accounts
python manage.py test tests.repairs
python manage.py test tests.workshop
python manage.py test tests.config
```

## Usuarios de prueba por rol

```powershell
python manage.py seed_test_users
```

El comando es idempotente y crea:

| Rol | Email | Contraseña |
| --- | --- | --- |
| Administrador | `admin@techpro.local` | `TechproTest!2026` |
| Técnico | `tecnico@techpro.local` | `TechproTest!2026` |
| Vendedor | `vendedor@techpro.local` | `TechproTest!2026` |
| Consulta | `consulta@techpro.local` | `TechproTest!2026` |

La contraseña puede cambiarse con `TECHPRO_TEST_PASSWORD` o `--password`. En
producción el comando exige `--force`.

## Estructura de la suite

```text
server/tests/
├── support.py                  # Usuarios, payloads y helpers
├── accounts/
│   ├── test_authentication.py  # Registro, JWT, CSRF, rate limit y logout
│   └── test_roles.py           # 401/403 por rol y comando de usuarios
├── repairs/
│   └── test_repairs_api.py     # CRUD y aislamiento de reparaciones
├── workshop/
│   ├── test_customers_api.py
│   ├── test_suppliers_api.py
│   ├── test_inventory_api.py
│   ├── test_sales_api.py
│   ├── test_reports_api.py
│   └── test_methods.py         # Contrato 405
└── config/                     # Entorno, base de datos y middleware
```

## Criterios de aceptación

- Todos los tests en estado `OK`.
- Sin errores de sistema (`manage.py check`).
- Cobertura de ramas ≥ 90 %.
- `400`, `401`, `403`, `404` y `405` cubiertos por recurso.
