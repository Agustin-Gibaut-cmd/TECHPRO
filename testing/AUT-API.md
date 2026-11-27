# AUT-API — Pruebas de contrato HTTP

## Requisitos

- Backend en ejecución.
- Usuarios de prueba creados.
- Base de datos migrada.

## Preparación

En una terminal:

```powershell
cd server
python manage.py migrate
python manage.py seed_test_users

# La suite hace varias solicitudes de login seguidas; subí el límite para evitar 429
$env:THROTTLE_RATE_LOGIN = "100/minute"

python manage.py runserver 127.0.0.1:8000
```

En otra terminal, desde la raíz:

```powershell
python -m unittest discover -s testing/api -v
```

## Variables opcionales

| Variable | Valor por defecto |
| --- | --- |
| `TECHPRO_API_URL` | `http://127.0.0.1:8000` |
| `TECHPRO_TEST_EMAIL` | `admin@techpro.local` |
| `TECHPRO_TEST_PASSWORD` | `TechproTest!2026` |
| `TECHPRO_READ_ONLY_EMAIL` | `consulta@techpro.local` |
| `THROTTLE_RATE_LOGIN` | `5/minute` en el servidor; usar `100/minute` para la suite |

Ejemplo:

```powershell
$env:TECHPRO_API_URL = "http://127.0.0.1:8000"
python -m unittest discover -s testing/api -v
```

## Casos cubiertos

| Test | Verifica |
| --- | --- |
| `test_health_check_is_public` | `GET /api/health/` responde 200 |
| `test_protected_endpoint_requires_authentication` | 401 sin sesión |
| `test_login_me_and_logout_flow` | Login, perfil y logout con cookies |
| `test_invalid_login_returns_401` | Credenciales inválidas |
| `test_repair_crud_flow` | Alta, listado, edición y baja de reparaciones |
| `test_read_only_role_cannot_write` | 403 para rol `consulta` |
| `test_unsupported_method_returns_405` | Contrato de métodos |

## Resultado esperado

Todos los tests en `OK`. Si el servidor no está disponible, el primer test
falla con un error de conexión; en ese caso verificá el puerto y el proceso de
Django.
