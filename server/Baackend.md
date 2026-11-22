# Backend Django (API-only)

El backend expone el API de autenticación, reparaciones, clientes, inventario,
proveedores, ventas, reportes y health check; no publica `/admin/` ni depende
de sesiones de navegador.

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
| `POST` | `/api/auth/register/` | Registra nombre, email y contraseña; establece cookies JWT HttpOnly. |
| `POST` | `/api/auth/login/` | Valida email/contraseña y establece cookies JWT HttpOnly. |
| `POST` | `/api/auth/token/refresh/` | Rota cookies JWT HttpOnly sin devolver tokens en el cuerpo. |
| `GET` | `/api/auth/me/` | Devuelve nombre y email del usuario autenticado. |
| `POST` | `/api/auth/logout/` | Revoca el refresh token disponible y elimina las cookies. |
| `GET` | `/api/repairs/` | Lista las reparaciones creadas por el usuario autenticado. |
| `POST` | `/api/repairs/` | Registra una reparación para el usuario autenticado. |
| `PUT`, `PATCH` | `/api/repairs/<id>/` | Actualiza una reparación propia sin modificar su propietario. |
| `GET`, `POST` | `/api/customers/` | Lista o registra clientes de la cuenta autenticada. |
| `GET`, `PATCH`, `PUT`, `DELETE` | `/api/customers/<id>/` | Consulta, actualiza o elimina un cliente propio. |
| `GET`, `POST` | `/api/suppliers/` | Lista o registra proveedores de la cuenta autenticada. |
| `GET`, `PATCH`, `PUT`, `DELETE` | `/api/suppliers/<id>/` | Consulta, actualiza o elimina un proveedor propio. |
| `GET`, `POST` | `/api/inventory/` | Lista o registra productos de la cuenta autenticada. |
| `GET`, `PATCH`, `PUT`, `DELETE` | `/api/inventory/<id>/` | Consulta, actualiza o elimina un producto propio. |
| `GET`, `POST` | `/api/sales/` | Lista o registra ventas propias por producto. |
| `GET`, `PATCH`, `PUT`, `DELETE` | `/api/sales/<id>/` | Consulta, actualiza o elimina una venta propia. |
| `GET` | `/api/reports/summary/` | Devuelve métricas agregadas y gráficos basados en los datos propios. |

El email se normaliza a minúsculas. Las contraseñas requieren al menos 12
caracteres y Django guarda su hash, nunca el valor recibido. Access y refresh
se envían en cookies `HttpOnly`; las escrituras exigen CSRF. Las respuestas de
la API usan `Cache-Control: no-store`. El endpoint de refresh rota las cookies y
logout puede revocar el refresh aunque el access haya vencido.
El login limita a cinco intentos anónimos por minuto y dirección IP; en
producción agregá también límites en el proxy o gateway, especialmente si
desplegás varios procesos.

Un `401` en `/api/auth/login/` indica que no se autenticó ese correo y
contraseña. Registrá primero la cuenta o verificá que exista y que las
credenciales sean correctas. Para cambiar la contraseña de una cuenta existente,
ejecutá desde `server` y escribí la nueva contraseña cuando Django la solicite:

```powershell
python manage.py changepassword correo@example.com
```

En una base de datos nueva y vacía, aplicá las migraciones antes de iniciar la
API:

```powershell
python manage.py migrate
```

Si la base ya tiene tablas creadas manualmente desde `database.sql` y Django
indica migraciones pendientes, no ejecutes `migrate` a ciegas: puede fallar con
tablas existentes como `auth_user`. Hacé un respaldo y reconciliá el esquema
con las migraciones antes de continuar; no borres tablas para ocultar el error.
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
No reutilices contraseñas de desarrollo; si una clave local fue compartida,
reemplazala y generá secretos Django/JWT nuevos e independientes.

## Autenticación y esquema

`accounts/serializers.py` valida datos, normaliza correos, aplica validadores
de contraseña y delega el hash a Django. `accounts/views.py` expone registro,
login, usuario actual y logout. JWT dura 15 minutos; el refresh dura 7 días y
se rota/revoca con la app de blacklist.

`python manage.py migrate` es la fuente de verdad del esquema Django. Las
migraciones crean las tablas de reparaciones, clientes, inventario, proveedores
y ventas. Cada cuenta solo puede acceder a sus propios registros; el servidor
asigna el propietario y no acepta ese dato desde el cliente. El SKU es único por
cuenta y los valores de stock, cantidad vendida y precio no pueden ser
negativos. `database.sql` es una referencia manual del esquema; no reemplaza
las migraciones ni incluye las tablas auxiliares de Django.

La creación y actualización aceptan cliente, teléfono, equipo, modelo y serie,
descripción de falla y estado (`received`, `diagnosing`, `in_progress`,
`waiting_parts`, `completed` o `delivered`). La API valida los campos, limita
las operaciones al propietario y requiere una sesión autenticada y el header
CSRF.

Clientes incluyen nombre y teléfono obligatorios; correo, domicilio y notas
son opcionales. Inventario incluye nombre, SKU, cantidad, stock mínimo y precio;
categorización y descripción son opcionales. Proveedores mantienen datos de
contacto. Cada venta registra producto, cantidad y precio unitario; el servidor
calcula el total y no modifica automáticamente el inventario. No hay registros
precargados: el usuario carga todos los datos desde las secciones.

El resumen de reportes calcula importes mensuales, productos más vendidos,
clientes, proveedores, stock e indicadores de reparaciones a partir de las
filas existentes del usuario. El gráfico incluye los últimos seis meses
calendario según `TIME_ZONE`, siempre muestra el mes actual aunque no tenga
ventas y completa esos períodos con cero. No guarda agregados duplicados en la
base.
`endpoint.md` contiene el inventario completo de rutas y métodos del MVP.

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
python manage.py test tests
```

Las pruebas Django estan separadas en `tests/accounts`, `tests/repairs` y
`tests/workshop`; cada paquete cubre los endpoints y reglas de su dominio.
