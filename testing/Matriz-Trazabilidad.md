# Matriz de trazabilidad

| Caso | Requisito verificado | Endpoint(s) | Test automatizado | Suite |
| --- | --- | --- | --- | --- |
| EF-01 | Disponibilidad y caché | `GET /api/health/` | `HealthCheckApiTests.test_health_check_returns_ok_status` | AUT-BE / AUT-API |
| EF-02 | Alta segura de cuentas | `POST /api/auth/register/` | `AuthenticationApiTests.test_registration_*` | AUT-BE |
| EF-03 | Ciclo de sesión JWT | `/api/auth/login/`, `/api/auth/me/`, `/api/auth/token/refresh/`, `/api/auth/logout/` | `AuthenticationApiTests.test_login_*`, `test_refresh_*`, `test_logout_*` | AUT-BE / AUT-API / AUT-E2E |
| EF-04 | CSRF en escrituras | `POST /api/auth/login/` | `test_login_rejects_requests_without_csrf_token` | AUT-BE |
| EF-05 | Autenticación y roles | Todos los recursos privados | `RoleAuthorizationTests.*`, `SeedTestUsersCommandTests.*` | AUT-BE |
| EF-06 | Reparaciones y aislamiento | `/api/repairs/` | `RepairApiTests.*` | AUT-BE / AUT-API |
| EF-07 | Clientes | `/api/customers/` | `CustomerApiTests.*` | AUT-BE |
| EF-08 | Proveedores | `/api/suppliers/` | `SupplierApiTests.*` | AUT-BE |
| EF-09 | Inventario | `/api/inventory/` | `InventoryApiTests.*` | AUT-BE |
| EF-10 | Ventas | `/api/sales/` | `SaleApiTests.*` | AUT-BE |
| EF-11 | Reportes | `/api/reports/summary/` | `ReportSummaryApiTests.*` | AUT-BE |
| EF-12 | Contrato de métodos | Todos | `HttpMethodContractTests.*` | AUT-BE |
| ACC | Criterios de aceptación | Flujo completo | Checklist manual | ACC |
