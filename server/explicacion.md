# Explicacion del backend TECHPRO

Directorio: server/

## Estructura general

- manage.py: punto de entrada de Django.
- config/: configuracion del proyecto.
  - settings.py: carga variables de entorno y arma la configuracion final.
  - settings_*.py: modulos separados para apps, auth, base de datos, HTTP, JWT, etc.
  - env/: parsers y validacion de variables de entorno.
  - urls.py: rutas principales del API.
  - database.py: construccion de la configuracion de PostgreSQL o SQLite.
- accounts/: autenticacion y autorizacion.
  - authentication.py: JWT en cookies HttpOnly y validacion CSRF.
  - serializers/: registro, login y serializacion de usuario.
  - views/: endpoints de auth, CSRF, perfil y logout.
  - roles.py: permisos por rol.
  - throttling.py: rate limiting de login.
- repairs/: gestion de ordenes de reparacion.
  - models.py: modelo Repair con validaciones y normalizacion.
  - serializers.py: serializacion de reparaciones.
  - views.py: CRUD filtrado por usuario autenticado.
  - urls.py: rutas de reparaciones.
  - migrations/: migraciones de la app.
- workshop/: operacion del taller.
  - models/: Customer, Supplier, InventoryItem y Sale.
  - serializers/: serializacion y validaciones de cada entidad.
  - views/: CRUD por propietario y reportes.
  - services.py: persistencia de inventario y deteccion de SKU duplicado.
  - reporting/: calculo de metricas, ventas mensuales y productos mas vendidos.
  - urls.py: rutas de workshop.
  - migrations/: migraciones de la app.
- tests/: suite de pruebas del backend.
  - accounts, config, repairs y workshop contienen tests de API y logica.
  - support.py: factories y payloads compartidos.

## Funcionamiento

1. El cliente consume endpoints bajo /api/.
2. Django valida autenticacion mediante cookies JWT HttpOnly.
3. Las vistas delegan en serializers para validar entrada.
4. Los modelos normalizan y validan datos antes de guardar en PostgreSQL.
5. Las consultas se filtran por el usuario autenticado para aislar datos.
6. Los reportes agregan ventas, stock, clientes, proveedores y reparaciones.

## Endpoints principales

- /api/health/: estado del servicio.
- /api/auth/: registro, login, refresh, perfil y logout.
- /api/repairs/: CRUD de reparaciones.
- /api/: clientes, proveedores, inventario, ventas y reportes.

## Base de datos

- Produccion: PostgreSQL.
- Desarrollo y pruebas: SQLite opcional con DEBUG=true.
- Las migraciones se aplican con python manage.py migrate.

## Seguridad

- Tokens JWT en cookies HttpOnly.
- Validacion CSRF en metodos que modifican estado.
- Rate limiting en login.
- Permisos por rol: admin, tecnico, vendedor y consulta.
- Aislamiento de datos por usuario propietario.