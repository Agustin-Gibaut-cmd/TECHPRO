# Casos de prueba — EF-01 a EF-12

Cada caso indica precondiciones, pasos y resultado esperado. La columna
**Automatización** referencia el test que lo cubre.

## EF-01 — Health check público

- **Objetivo:** confirmar disponibilidad del backend sin autenticación.
- **Precondiciones:** servidor levantado.
- **Pasos:** `GET /api/health/`.
- **Esperado:** `200` con `{"status": "ok"}` y `Cache-Control: no-store`.
- **Automatización:** `tests.config.test_config.HealthCheckApiTests`, `AUT-API`.

## EF-02 — Registro de usuario

- **Objetivo:** crear una cuenta válida y rechazar datos inseguros.
- **Precondiciones:** email no registrado.
- **Pasos:** `POST /api/auth/register/` con nombre, email y contraseña; repetir con
  contraseña corta, numérica, similar al email o email duplicado.
- **Esperado:** `201` con usuario y cookies HttpOnly en el caso válido; `400` en
  cada validación.
- **Automatización:** `tests.accounts.test_authentication`.

## EF-03 — Login, refresh y logout

- **Objetivo:** verificar el ciclo de sesión JWT.
- **Precondiciones:** usuario de prueba creado.
- **Pasos:** `POST /api/auth/login/`, `GET /api/auth/me/`,
  `POST /api/auth/token/refresh/`, `POST /api/auth/logout/`.
- **Esperado:** `200`, `200`, `204` y `204`; cookies HttpOnly; tokens no expuestos
  en el body; refresh rotado y logout con cookies expiradas.
- **Automatización:** `tests.accounts.test_authentication`, `AUT-API`, `AUT-E2E`.

## EF-04 — Protección CSRF

- **Objetivo:** impedir escrituras sin token CSRF.
- **Precondiciones:** cliente con `enforce_csrf_checks`.
- **Pasos:** `POST /api/auth/login/` sin `X-CSRFToken`.
- **Esperado:** `403`.
- **Automatización:** `tests.accounts.test_authentication`.

## EF-05 — Autenticación y roles

- **Objetivo:** validar 401 sin sesión y 403 por rol.
- **Precondiciones:** usuarios `consulta`, `admin`, `tecnico` y `vendedor`.
- **Pasos:** `GET` a recursos sin autenticación; `POST` con rol `consulta`;
  `POST` con roles operativos.
- **Esperado:** `401` sin sesión; `403` para `consulta`; `201` para roles
  operativos.
- **Automatización:** `tests.accounts.test_roles`.

## EF-06 — Reparaciones

- **Objetivo:** validar CRUD, normalización y aislamiento.
- **Precondiciones:** usuario autenticado.
- **Pasos:** `POST`, `GET`, `PUT`, `PATCH` y `DELETE` en `/api/repairs/`;
  intentar acceder a una reparación de otro usuario.
- **Esperado:** `201`, `200`, `200`, `200`, `204`; serial en mayúsculas; `400` en
  campos inválidos; `404` para registros ajenos.
- **Automatización:** `tests.repairs.test_repairs_api`, `AUT-API`.

## EF-07 — Clientes

- **Objetivo:** validar CRUD y validaciones de contacto.
- **Precondiciones:** usuario autenticado.
- **Pasos:** crear cliente, editar, listar, eliminar; enviar email inválido y
  omitir campos obligatorios.
- **Esperado:** `201`, `200`, `200`, `204`; `400` con `email`, `name` o `phone`.
- **Automatización:** `tests.workshop.test_customers_api`.

## EF-08 — Proveedores

- **Objetivo:** validar CRUD y validaciones de proveedores.
- **Precondiciones:** usuario autenticado.
- **Pasos:** crear, editar, listar y eliminar; enviar email inválido y omitir
  campos obligatorios.
- **Esperado:** `201`, `200`, `200`, `204`; `400` en validaciones.
- **Automatización:** `tests.workshop.test_suppliers_api`.

## EF-09 — Inventario

- **Objetivo:** validar SKU, stock y precios.
- **Precondiciones:** usuario autenticado.
- **Pasos:** crear con SKU en minúsculas, repetir SKU, actualizar conservando el
  SKU, usar stock 0, precio 0 y precio negativo.
- **Esperado:** SKU en mayúsculas; `400` en duplicado o precio negativo; `201`
  con stock 0; `200` al editar.
- **Automatización:** `tests.workshop.test_inventory_api`.

## EF-10 — Ventas

- **Objetivo:** validar cálculo de total y precisión decimal.
- **Precondiciones:** usuario autenticado.
- **Pasos:** crear venta con cantidad y precio; editar cantidad; enviar cantidad
  0 o precio negativo; intentar inyectar `total` o `created_by_id`.
- **Esperado:** total calculado en servidor; `400` en cantidad o precio inválido;
  campos de solo lectura ignorados.
- **Automatización:** `tests.workshop.test_sales_api`.

## EF-11 — Reportes

- **Objetivo:** validar métricas y aislamiento por usuario.
- **Precondiciones:** datos propios y de otro usuario.
- **Pasos:** `GET /api/reports/summary/` con y sin datos; simular cambio de año.
- **Esperado:** solo datos propios; series de 6 meses continuas; totales y
  promedios correctos; `200` y `no-store`.
- **Automatización:** `tests.workshop.test_reports_api`.

## EF-12 — Métodos HTTP no permitidos

- **Objetivo:** validar el contrato de verbos.
- **Precondiciones:** usuario autenticado para recursos privados.
- **Pasos:** enviar `PUT`/`DELETE` a colecciones, `POST` a detalles y métodos no
  soportados en auth, reportes y salud.
- **Esperado:** `405` en todos los casos.
- **Automatización:** `tests.workshop.test_methods`.
