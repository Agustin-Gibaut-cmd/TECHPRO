TECHPRO

QUE CONTIENE

Frontend Angular con formularios para crear una cuenta e iniciar sesion,
dashboard protegido, secciones de reparaciones, clientes e inventario con
formularios y tablas conectadas al servidor, manejo de JWT mediante cookies y
renderizado SSR con Node.

Backend API-only Django REST Framework conectado a PostgreSQL. Incluye registro,
login, renovacion y revocacion de tokens, endpoint de usuario actual y health
check, ademas de endpoints autenticados para reparaciones, clientes e inventario;
no expone el admin ni usa sesiones de navegador. Django valida las contrasenas
y guarda solamente sus hashes.

ARCHIVOS PRINCIPALES

server/accounts/serializers.py valida y normaliza los datos de autenticacion.
server/accounts/views.py implementa las rutas del API.
server/repairs/models.py define la tabla de reparaciones.
server/repairs/views.py lista y crea reparaciones del usuario autenticado.
server/workshop/models.py define clientes y productos de inventario.
server/workshop/views.py ofrece operaciones CRUD privadas por usuario.
server/config/settings.py configura seguridad, base de datos, CORS y JWT.
client/src/app/auth.service.ts maneja la sesion del frontend.
client/src/app/repairs/repairs.ts conecta el formulario y la tabla al API.
client/src/app/customers/customers.ts conecta clientes al API.
client/src/app/inventory/inventory.ts conecta el inventario al API.
client/src/app/auth.interceptor.ts envia cookies y renueva la sesion.
client/src/server.ts sirve Angular SSR y establece headers de seguridad.
database.sql contiene el esquema SQL manual de autenticacion, reparaciones,
clientes e inventario.

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

Clientes e inventario requieren autenticacion. El servidor asigna el propietario
de cada registro y solo devuelve, modifica o elimina registros de ese usuario.
Cada cuenta debe usar un SKU distinto para cada producto; las cantidades y el
precio unitario no pueden ser negativos.

En produccion usa DEBUG=false, secretos distintos y aleatorios, hosts y
origenes HTTPS explicitos, PostgreSQL con TLS, HTTPS/HSTS y un usuario de base
de datos con privilegios minimos. Consulta los README de server y client para
los detalles y comandos de pruebas.
