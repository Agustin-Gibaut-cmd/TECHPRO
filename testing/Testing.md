# Testing TECHPRO — Índice de casos EF-01 a EF-12

Documentación de verificación y validación para el examen final libre
`VyV-Final-Gibaut-Agustin`. El alcance cubre autenticación, autorización por
rol, reparaciones, clientes, proveedores, inventario, ventas y reportes.

## Suites

| Suite | Tipo | Herramienta | Comando |
| --- | --- | --- | --- |
| `AUT-BE` | Automatizada de backend | Django `manage.py test` + `coverage` | `cd server && coverage run --branch manage.py test && coverage report -m` |
| `AUT-API` | Automatizada de contrato HTTP | Python `unittest` + `urllib` | `python -m unittest discover -s testing/api -v` |
| `AUT-E2E` | Automatizada end-to-end | Playwright | `cd testing/e2e && npm test` |
| `ACC` | Aceptación manual | Checklist | Ver [`ACC.md`](ACC.md) |

## Índice de casos

| ID | Caso | Prioridad | Automatización | Evidencia manual |
| --- | --- | --- | --- | --- |
| [EF-01](Casos-de-Prueba.md#ef-01--health-check-público) | Health check público | Alta | `tests.config.test_config.HealthCheckApiTests`, `AUT-API` | `ACC.md` |
| [EF-02](Casos-de-Prueba.md#ef-02--registro-de-usuario) | Registro de usuario y validación de contraseña | Alta | `tests.accounts.test_authentication` | `ACC.md` |
| [EF-03](Casos-de-Prueba.md#ef-03--login-refresh-y-logout) | Login, refresh y logout con cookies HttpOnly | Alta | `tests.accounts.test_authentication`, `AUT-API`, `AUT-E2E` | `ACC.md` |
| [EF-04](Casos-de-Prueba.md#ef-04--protección-csrf) | Protección CSRF en escrituras | Alta | `tests.accounts.test_authentication` | `ACC.md` |
| [EF-05](Casos-de-Prueba.md#ef-05--autenticación-y-roles) | 401 sin sesión y 403 por rol de consulta | Alta | `tests.accounts.test_roles` | `ACC.md` |
| [EF-06](Casos-de-Prueba.md#ef-06--reparaciones) | Reparaciones: CRUD, normalización y aislamiento | Alta | `tests.repairs.test_repairs_api`, `AUT-API` | `ACC.md` |
| [EF-07](Casos-de-Prueba.md#ef-07--clientes) | Clientes: CRUD, validaciones y aislamiento | Media | `tests.workshop.test_customers_api` | `ACC.md` |
| [EF-08](Casos-de-Prueba.md#ef-08--proveedores) | Proveedores: CRUD y validaciones | Media | `tests.workshop.test_suppliers_api` | `ACC.md` |
| [EF-09](Casos-de-Prueba.md#ef-09--inventario) | Inventario: SKU, stock y precios | Alta | `tests.workshop.test_inventory_api` | `ACC.md` |
| [EF-10](Casos-de-Prueba.md#ef-10--ventas) | Ventas: total y precisión decimal | Alta | `tests.workshop.test_sales_api` | `ACC.md` |
| [EF-11](Casos-de-Prueba.md#ef-11--reportes) | Reportes: métricas y aislamiento | Media | `tests.workshop.test_reports_api` | `ACC.md` |
| [EF-12](Casos-de-Prueba.md#ef-12--métodos-http-no-permitidos) | Métodos HTTP no permitidos (405) | Media | `tests.workshop.test_methods` | `ACC.md` |

## Orden sugerido de ejecución

1. `AUT-BE`: valida lógica, permisos, serializers y persistencia.
2. `AUT-API`: valida el contrato HTTP real con el servidor levantado.
3. `AUT-E2E`: valida el flujo de login y la protección de rutas en Angular.
4. `ACC`: confirma la experiencia de usuario y los criterios de aceptación.

## Documentos

- [Plan de pruebas](Plan-de-Pruebas.md)
- [Casos de prueba detallados](Casos-de-Prueba.md)
- [Matriz de trazabilidad](Matriz-Trazabilidad.md)
- [Registro de ejecución](Registro-Ejecucion.md)
- [Reporte de defectos](Reporte-Defectos.md)
- [Plantilla de caso de prueba](Plantilla-Caso-Prueba.md)
- [AUT-BE](AUT-BE.md) · [AUT-API](AUT-API.md) · [AUT-E2E](AUT-E2E.md) · [ACC](ACC.md)
