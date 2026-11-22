# Endpoints de TECHPRO

## Resumen

- **7 áreas:** autenticación, reparaciones, clientes, inventario, proveedores,
  ventas y reportes.
- **18 rutas** y **36 métodos de negocio documentados** (sin contar `HEAD` ni
  `OPTIONS`, que Django puede agregar automáticamente).
- **Sin datos precargados:** cada cuenta crea sus propios registros.
- Los datos privados se filtran en el servidor por el usuario autenticado.
- Los endpoints de escritura requieren cookies de sesión y protección CSRF.

La app usa migraciones Django como fuente de verdad. `database.sql` es una
referencia manual del esquema y no reemplaza `python manage.py migrate`.

## Autenticación

| Método | Ruta | Acceso | Uso |
| --- | --- | --- | --- |
| `GET` | `/api/auth/csrf/` | Público | Obtiene el token CSRF para las solicitudes de escritura. |
| `POST` | `/api/auth/register/` | Público + CSRF | Registra una cuenta y establece cookies JWT HttpOnly. |
| `POST` | `/api/auth/login/` | Público + CSRF | Inicia sesión y establece cookies JWT HttpOnly. |
| `POST` | `/api/auth/token/refresh/` | Cookie + CSRF | Renueva y rota cookies sin devolver tokens en el cuerpo. |
| `GET` | `/api/auth/me/` | Autenticado | Devuelve nombre y correo de la cuenta actual. |
| `POST` | `/api/auth/logout/` | Cookie + CSRF | Revoca el refresh token y limpia cookies; funciona aunque haya vencido el access. |

Las cookies de autenticación son `HttpOnly`; el access se limita a `/api/` y
el refresh a `/api/auth/`. Todas las respuestas bajo `/api/` incluyen
`Cache-Control: no-store`.

## Reparaciones

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/repairs/` | Lista las reparaciones propias. |
| `POST` | `/api/repairs/` | Registra una reparación propia. |
| `PUT`, `PATCH` | `/api/repairs/<id>/` | Actualiza una reparación propia. |

## Clientes

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/customers/` | Lista clientes propios. |
| `POST` | `/api/customers/` | Crea un cliente. |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/customers/<id>/` | Consulta, actualiza o elimina un cliente propio. |

## Inventario

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/inventory/` | Lista productos propios. |
| `POST` | `/api/inventory/` | Crea un producto. |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/inventory/<id>/` | Consulta, actualiza o elimina un producto propio. |

El SKU se normaliza a mayúsculas y es único dentro de la cuenta. Cantidades,
stock mínimo y precios no pueden ser negativos.

## Proveedores

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/suppliers/` | Lista proveedores propios. |
| `POST` | `/api/suppliers/` | Crea un proveedor. |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/suppliers/<id>/` | Consulta, actualiza o elimina un proveedor propio. |

Los proveedores guardan nombre y teléfono obligatorios; correo, domicilio y
notas son opcionales.

## Ventas

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/sales/` | Lista ventas propias, de más reciente a más antigua. |
| `POST` | `/api/sales/` | Registra una venta por producto. |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/sales/<id>/` | Consulta, actualiza o elimina una venta propia. |

Cada venta registra producto, cantidad y precio unitario; el nombre del cliente
es opcional. El total se calcula en el servidor como cantidad por precio. Este
registro simple no descuenta ni modifica automáticamente el inventario.

## Reportes

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/reports/summary/` | Devuelve indicadores y series para los gráficos de la cuenta actual. |

La respuesta resume cantidad e importe de ventas, promedio por registro,
ventas agrupadas por mes, productos más vendidos, clientes, proveedores,
productos y unidades en inventario, valor estimado del inventario, stock bajo y
reparaciones abiertas. Las series se calculan desde las tablas existentes; no
se generan registros de ejemplo ni se guardan totales duplicados.

## Tablas principales

- `auth_user`: cuentas del sistema.
- `repairs_repair`: órdenes de reparación.
- `workshop_customer`: clientes.
- `workshop_inventoryitem`: productos y stock.
- `workshop_supplier`: proveedores.
- `workshop_sale`: registros de ventas.
- `token_blacklist_outstandingtoken` y
  `token_blacklist_blacklistedtoken`: revocación y rotación de refresh JWT.

Reportes son consultas agregadas y no tienen una tabla propia.
