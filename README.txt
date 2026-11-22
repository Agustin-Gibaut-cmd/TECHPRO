TECHPRO

QUE CONTIENE

Frontend Angular con formularios para crear una cuenta e iniciar sesion,
dashboard protegido, manejo de access y refresh JWT y renderizado SSR con Node.

Backend API-only Django REST Framework conectado a PostgreSQL. Incluye registro,
login, renovacion y revocacion de tokens, endpoint de usuario actual y health
check; no expone el admin ni usa sesiones de navegador. Django valida las
contrasenas y guarda solamente sus hashes.

ARCHIVOS PRINCIPALES

server/accounts/serializers.py valida y normaliza los datos de autenticacion.
server/accounts/views.py implementa las rutas del API.
server/config/settings.py configura seguridad, base de datos, CORS y JWT.
client/src/app/auth.service.ts maneja la sesion del frontend.
client/src/app/auth.interceptor.ts agrega el token y renueva access tokens.
client/src/server.ts sirve Angular SSR y establece headers de seguridad.
database.sql contiene el esquema SQL reducido de autenticacion.

INICIO LOCAL

1. Segui server/README.md para crear el entorno Python, configurar server/.env,
   aplicar migraciones e iniciar Django en localhost:8000.
2. Desde client, ejecuta npm install y npm start.
3. Abri http://localhost:4200.

CONFIGURACION Y SECRETOS

El backend carga server/.env con python-dotenv. Ese archivo esta ignorado por
Git. Usa server/.env.example como guia y genera secretos propios.

Angular no usa dotenv. Los archivos src/environments se compilan en JavaScript
y solo pueden contener configuracion publica, nunca claves ni contrasenas. En
produccion Angular usa /api y requiere un proxy HTTPS hacia Django.

SEGURIDAD Y PUNTOS PENDIENTES

No subas archivos .env, tokens, contrasenas, dumps de datos o claves privadas.
Si algun secreto se subio antes, rotalo: ignorar el archivo no lo borra del
historial de Git.

Los JWT se transmiten en cookies HttpOnly y no se guardan en localStorage. Las
operaciones de escritura requieren CSRF. XSS todavia podria actuar dentro de la
sesion; antes de produccion configura CSP en el proxy y evita HTML no confiable.

En produccion usa DEBUG=false, secretos distintos y aleatorios, hosts y
origenes HTTPS explicitos, PostgreSQL con TLS, HTTPS/HSTS y un usuario de base
de datos con privilegios minimos. Consulta los README de server y client para
los detalles y comandos de pruebas.
