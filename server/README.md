# Backend Django (API-only)

El backend expone solo el API de autenticación y health check; no publica
`/admin/` ni depende de sesiones de navegador.

## Desarrollo local

Requiere Python 3.10+ y PostgreSQL. Desde la raíz:

```powershell
Set-Location .\server
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Creá la base y un usuario local en `psql` como administrador:

```sql
CREATE ROLE workshop WITH LOGIN;
\password workshop
CREATE DATABASE workshop OWNER workshop;
```

`\password` pide la contraseña sin dejarla en el historial del comando. Poné
ese valor en `DB_PASSWORD` dentro de `server/.env`. No uses el usuario
administrador `postgres` para la conexión habitual de la aplicación.

Generá dos secretos distintos y reemplazá los marcadores del `.env` local:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Usá una salida para `DJANGO_SECRET_KEY` y otra para `JWT_SIGNING_KEY`. No
reutilices estos valores en producción. Aplicá el esquema y arrancá:

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

El API local queda en `http://127.0.0.1:8000/api/`; la comprobación de salud
está en `/api/health/`.

## API disponible

| Método | Ruta | Función |
| --- | --- | --- |
| `GET` | `/api/health/` | Confirma que Django responde; no comprueba la base de datos. |
| `GET` | `/api/auth/csrf/` | Prepara la cookie CSRF y devuelve el valor que el cliente envía en el header. |
| `POST` | `/api/auth/register/` | Registra nombre, email y contraseña; responde con usuario y JWT. |
| `POST` | `/api/auth/login/` | Valida email/contraseña y responde con usuario y JWT. |
| `POST` | `/api/auth/token/refresh/` | Rota el refresh token y entrega nuevos tokens. |
| `GET` | `/api/auth/me/` | Devuelve nombre y email del usuario autenticado. |
| `POST` | `/api/auth/logout/` | Revoca el refresh token de la sesión autenticada. |

El email se normaliza a minúsculas. Las contraseñas requieren al menos 12
caracteres y Django guarda su hash, nunca el valor recibido. Access y refresh
se envían en cookies `HttpOnly`; las escrituras exigen CSRF. El endpoint de
refresh rota la cookie y logout la revoca.

## Variables de entorno

`config/settings.py` carga `server/.env` con `python-dotenv`. Las variables ya
definidas en el entorno del proceso tienen prioridad sobre el archivo. `.env`
es local y está ignorado por Git; `.env.example` contiene solo valores de
desarrollo y marcadores, nunca secretos reales.

| Variable | Uso |
| --- | --- |
| `DJANGO_SECRET_KEY` | Secreto interno de Django; mínimo 50 caracteres. |
| `JWT_SIGNING_KEY` | Firma JWT; distinto del secreto Django. |
| `DEBUG` | `true` solo en desarrollo local. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos por Django, separados por comas. |
| `DB_ENGINE` | Backend de base de datos; usar `postgresql`. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Conexión PostgreSQL. |
| `DB_SSLMODE` | En desarrollo local puede ser `prefer`; producción requiere `require`, `verify-ca` o `verify-full`. |
| `CORS_ALLOWED_ORIGINS` | Orígenes exactos del frontend, separados por comas. |
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables de Django. |
| `SECURE_SSL_REDIRECT` | Redirige HTTP a HTTPS; activado por defecto fuera de desarrollo. |
| `TRUST_X_FORWARDED_PROTO` | Activar solo detrás de un proxy confiable que sobrescriba ese header. |
| `SECURE_HSTS_SECONDS` | Duración HSTS; configurar cuidadosamente al habilitar HTTPS. |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` | Desactivados por defecto; activalos solo si todo el dominio y sus subdominios sirven HTTPS. |
| `PORT`, `HOST` | Solo el servidor SSR de Angular; Node recibe estos valores del entorno del proceso. |

Las variables sensibles se validan al arrancar. En producción Django rechaza
secretos con prefijo `dev-`, hosts vacíos o comodín, orígenes CORS locales y
una conexión PostgreSQL sin TLS. No copies el `.env.example` sin modificarlo:
allí `DEBUG=true`, TLS y HSTS están configurados para desarrollo local. En
producción usá `DEBUG=false`, `SECURE_SSL_REDIRECT=true`, un
`SECURE_HSTS_SECONDS` mayor a cero y los hosts/orígenes reales.

## Autenticación y esquema

`accounts/serializers.py` valida datos, normaliza correos, aplica validadores
de contraseña y delega el hash a Django. `accounts/views.py` expone registro,
login, usuario actual y logout. JWT dura 15 minutos; el refresh dura 7 días y
se rota/revoca con la app de blacklist.

`python manage.py migrate` es la fuente de verdad del esquema Django. El
`database.sql` de la raíz es un esquema reducido de autenticación; no reemplaza
las migraciones generales ni incluye el registro de migraciones y tablas
auxiliares de Django.

## Producción: puntos frágiles

- Usá `DEBUG=false`, secretos aleatorios nuevos, hosts y orígenes reales, TLS
  para PostgreSQL y HTTPS en el proxy.
- HSTS debe configurarse solo cuando HTTPS funcione en todo el dominio. Si TLS
  termina en un proxy, confiá en `X-Forwarded-Proto` únicamente si el proxy lo
  sobrescribe y no permite que el cliente controle ese header.
- Creá un rol PostgreSQL dedicado con privilegios mínimos; no uses `postgres`.
- `SECURE_HSTS_PRELOAD` y `SECURE_HSTS_INCLUDE_SUBDOMAINS` quedan apagados por
  defecto: activarlos afecta todos los subdominios.
- Si TLS termina en un proxy, configurá `TRUST_X_FORWARDED_PROTO=true` solo si
  ese proxy elimina y vuelve a establecer `X-Forwarded-Proto`.
- CORS no reemplaza autenticación ni protección contra XSS. Aunque los JWT sean
  `HttpOnly`, una vulnerabilidad XSS aún podría realizar solicitudes desde la
  sesión del usuario. Definí CSP en el proxy y evitá HTML no confiable.
- Los throttles DRF predeterminados no sustituyen límites distribuidos en un
  despliegue con varios procesos. Agregá rate limiting en proxy/cache para
  login y registro.

Ejecutá pruebas y comprobaciones desde `server`:

```powershell
python manage.py check
python manage.py test accounts.tests
```
