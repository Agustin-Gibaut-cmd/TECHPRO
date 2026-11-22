TECHPRO
Sistema de gestion para talleres de reparacion y servicio tecnico.

DESCRIPCION

TECHPRO permite administrar reparaciones, clientes, inventario, proveedores y
ventas desde una aplicacion web. La seccion de reportes calcula indicadores y
graficos a partir de los registros reales de cada cuenta. El sistema no carga
datos de ejemplo.

El frontend esta desarrollado con Angular y TypeScript. El backend usa Django,
Django REST Framework y PostgreSQL. La autenticacion usa JWT en cookies
HttpOnly; el cliente no guarda tokens en localStorage. Las rutas de escritura
requieren proteccion CSRF y el servidor limita cada registro a su propietario.

ARQUITECTURA DEL REPOSITORIO

client/
    Aplicacion Angular, pruebas de componentes y servidor de renderizado SSR.
    client/src/app/auth-form contiene el formulario compartido de acceso y
    registro.
    client/src/app/customers administra clientes.
    client/src/app/dashboard integra las secciones.
    client/src/app/inventory administra productos y existencias.
    client/src/app/login maneja inicio de sesion y registro.
    client/src/app/repairs administra ordenes de reparacion.
    client/src/app/reports muestra indicadores y graficos.
    client/src/app/sales administra registros de ventas.
    client/src/app/suppliers administra proveedores.
    client/src/environments contiene configuracion publica del API, no secretos.

server/
    API Django y configuracion de PostgreSQL, JWT, CSRF, CORS y seguridad.
    server/accounts contiene registro, login, refresh, logout y autenticacion.
    server/repairs contiene modelos, validaciones y API de reparaciones.
    server/workshop contiene clientes, inventario, proveedores, ventas y
    agregaciones de reportes.
    server/config contiene settings, rutas y middleware.
    Las migraciones Django son la fuente oficial del esquema.

tests/
    Ejecutor central de comprobaciones y guia de validacion.
    Las pruebas Angular permanecen junto a sus componentes.

server/tests/
    Pruebas Django separadas del codigo de produccion y organizadas por dominio:
    accounts, repairs y workshop.

database.sql
    Referencia manual de las tablas principales de la aplicacion.
    No reemplaza las migraciones Django ni incluye todas las tablas internas
    auxiliares de Django.

endpoint.md
    Inventario de rutas, metodos, modulos y tablas principales del MVP.

REQUISITOS

Python 3.10 o posterior, PostgreSQL, Node.js y npm compatibles con las
versiones indicadas en server/requirements.txt y client/package.json.

INICIO DEL BACKEND

Crear un rol y una base de datos en PostgreSQL. Estos comandos se ejecutan en
psql como administrador:

    CREATE ROLE workshop WITH LOGIN;
    \password workshop
    CREATE DATABASE workshop OWNER workshop;

Desde PowerShell, crear el entorno e instalar dependencias:

    Set-Location .\server
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    Copy-Item .env.example .env

Editar server/.env con las credenciales locales de PostgreSQL. Generar dos
secretos distintos con este comando y guardarlos en DJANGO_SECRET_KEY y
JWT_SIGNING_KEY:

    python -c "import secrets; print(secrets.token_urlsafe(64))"

No usar secretos de desarrollo en produccion ni copiar server/.env al
repositorio. El archivo server/.env.example contiene valores de ejemplo y
marcadores, no credenciales funcionales.

Aplicar migraciones e iniciar Django:

    python manage.py migrate
    python manage.py runserver 127.0.0.1:8000

El API local queda en http://127.0.0.1:8000/api/. Su endpoint de salud es
/api/health/.

INICIO DEL FRONTEND

En una segunda terminal:

    Set-Location .\client
    npm install
    npm start

Abrir http://localhost:4200. La configuracion local apunta a
http://localhost:8000/api. Produccion usa /api en el mismo origen; el proxy
HTTPS debe reenviar esa ruta al servidor Django.

BASE DE DATOS Y REPORTES

Usar python manage.py migrate para crear y actualizar el esquema. database.sql
es una referencia manual que se ejecuta conectado a la base ya creada. Los
reportes se calculan con consultas sobre ventas, inventario, clientes,
proveedores y reparaciones; no se guarda una tabla de agregados.

Las ventas registran un producto, cantidad y precio unitario. El servidor
calcula el total. Por ahora una venta no descuenta existencias ni se vincula
automaticamente a un registro de inventario o cliente.

PRUEBAS Y VALIDACION

Desde la raiz del repositorio, ejecutar:

    .\tests\run-validation.ps1

El ejecutor comprueba la configuracion Django, que no falten migraciones,
prueba los endpoints, ejecuta las pruebas Angular, genera el build de
produccion y revisa espacios del diff.

La base PostgreSQL configurada debe estar disponible y el usuario de pruebas
debe poder crear una base temporal. Las dependencias deben estar instaladas
antes de ejecutar el script.

La ejecucion manual es:

    En server:
    python manage.py check
    python manage.py makemigrations --check --dry-run
    python manage.py test tests

    En client:
    npm test -- --watch=false
    npm run build

SEGURIDAD Y PRODUCCION

No subir archivos .env, contrasenas, tokens, certificados privados, dumps de
base ni datos personales. Si un secreto se publico alguna vez, rotarlo; dejar
de seguir el archivo no elimina el secreto del historial de Git.

La configuracion de Angular se incluye en el bundle y no debe contener
secretos. En produccion configurar DEBUG=false, secretos aleatorios distintos,
hosts y origenes HTTPS exactos, PostgreSQL con TLS, HTTPS en el proxy y un rol
de base de datos con privilegios minimos. Habilitar HSTS solo despues de
verificar HTTPS en todo el dominio. Definir CSP y rate limiting en la
infraestructura de despliegue.

Para consultar las variables, endpoints y precauciones detalladas, revisar
server/README.md, client/README.md y endpoint.md.
