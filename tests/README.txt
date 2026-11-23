TECHPRO - VALIDACION DEL PROYECTO

PROPOSITO

Esta carpeta contiene el ejecutor central de las validaciones del proyecto.
Los casos Angular permanecen junto a sus componentes. Las pruebas Django estan
separadas del codigo de produccion en server/tests y organizadas por dominio.

ARCHIVOS

run-validation.ps1
    Ejecuta comprobaciones Django, pruebas del API, pruebas de componentes
    Angular, build de produccion y git diff --check. Devuelve codigo 0 si todo
    pasa y codigo 1 si alguna etapa falla.

COBERTURA ACTUAL

Frontend:
    client/src/app/*.spec.ts
    Prueba rutas, autenticacion, formulario compartido, interceptor, dashboard
    y componentes de reparaciones, clientes, inventario, proveedores, ventas
    y reportes.

Backend:
    server/tests/accounts/test_authentication.py
    Prueba registro, login, cookies JWT HttpOnly, CSRF, refresh, usuario actual,
    logout y revocacion.

    server/tests/repairs/test_repairs_api.py
    Prueba aislamiento por propietario, autenticacion, validacion y
    actualizacion de reparaciones.

    server/tests/workshop/test_workshop_api.py
    Prueba clientes, inventario, proveedores, ventas, validaciones, permisos,
    calculos de reportes y aislamiento de datos entre cuentas.

REQUISITOS PARA EJECUTAR

1. PostgreSQL debe estar iniciado y server/.env debe tener una conexion local
   valida.
2. El usuario PostgreSQL configurado debe poder crear la base temporal que
   Django usa para las pruebas.
3. Las dependencias Python deben estar instaladas en server/.venv o disponibles
   en el Python activo.
4. Las dependencias Node deben estar instaladas en client/node_modules.
5. PowerShell debe poder ejecutar el archivo local.

COMO EJECUTAR

Desde la raiz del repositorio:

    .\tests\run-validation.ps1

La ejecucion no modifica datos de desarrollo. Django crea y elimina su propia
base temporal de pruebas. El build Angular escribe los artefactos ignorados en
client/dist.

EJECUCION MANUAL

Backend, desde server:

    python manage.py check
    python manage.py makemigrations --check --dry-run
    python manage.py test tests

Frontend, desde client:

    npm test -- --watch=false
    npm run build

ALCANCE

Estas pruebas son unitarias y de API con base de datos de prueba. No reemplazan
una prueba manual del despliegue, proxy HTTPS, cookies entre dominios ni
servicios externos de produccion.
