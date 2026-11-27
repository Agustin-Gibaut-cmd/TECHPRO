# Plan de pruebas — TECHPRO

## 1. Objetivo

Verificar que TECHPRO cumpla los requisitos funcionales y de seguridad del
examen final libre, con evidencia reproducible para backend, API, interfaz y
aceptación.

## 2. Alcance

Incluido:

- Autenticación JWT en cookies HttpOnly, CSRF y rate limiting de login.
- Autorización por autenticación y por rol (`admin`, `tecnico`, `vendedor`, `consulta`).
- CRUD y aislamiento por usuario en reparaciones, clientes, proveedores,
  inventario y ventas.
- Cálculo de totales, normalización de datos y validaciones de serializer.
- Reportes consolidados y series mensuales.
- Contrato HTTP: códigos 200, 201, 204, 400, 401, 403, 404 y 405.
- Flujo de login y protección de rutas en Angular.

Fuera de alcance:

- Pruebas de carga, estrés o penetración.
- Compatibilidad con navegadores distintos de Chromium en `AUT-E2E`.
- Servicios externos de correo, pagos o facturación electrónica.

## 3. Estrategia

| Nivel | Objetivo | Herramienta |
| --- | --- | --- |
| Unitario / integración backend | Lógica de dominio, serializers, permisos y persistencia | Django `APITestCase` |
| Contrato API | Verificar endpoints reales y cookies | `unittest` + `urllib` |
| End-to-end | Flujo de usuario en navegador | Playwright |
| Aceptación | Validar criterios de negocio | Checklist manual |

## 4. Ambientes

- **Local backend:** SQLite para pruebas rápidas o PostgreSQL para paridad.
- **API:** servidor Django en `http://127.0.0.1:8000`.
- **Frontend:** Angular en `http://127.0.0.1:4200`.
- **Datos:** usuarios de prueba creados con `seed_test_users`; la suite backend
  usa una base temporal y no modifica datos reales.

## 5. Datos y roles de prueba

| Rol | Email | Contraseña | Permisos |
| --- | --- | --- | --- |
| Administrador | `admin@techpro.local` | `TechproTest!2026` | Acceso completo |
| Técnico | `tecnico@techpro.local` | `TechproTest!2026` | Acceso completo |
| Vendedor | `vendedor@techpro.local` | `TechproTest!2026` | Acceso completo |
| Consulta | `consulta@techpro.local` | `TechproTest!2026` | Solo lectura |

Los valores son de prueba y pueden cambiarse con `TECHPRO_TEST_PASSWORD`.

## 6. Criterios de entrada

- Dependencias instaladas (`requirements.txt`, `npm install`).
- Migraciones aplicadas.
- Usuarios de prueba creados.
- Backend y frontend disponibles para `AUT-API` y `AUT-E2E`.

## 7. Criterios de salida

- `AUT-BE` finaliza con 0 fallos.
- Cobertura de ramas del backend igual o superior a 90 %.
- `AUT-API` finaliza sin fallos contra el servidor local.
- `AUT-E2E` valida login y redirección de ruta privada.
- `ACC` sin defectos bloqueantes abiertos.

## 8. Riesgos

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| PostgreSQL no disponible | Bloquea pruebas locales | Usar `DB_ENGINE=sqlite` |
| Rate limiting interfiere con pruebas | Falsos 429 | `cache.clear()` en `setUp` |
| Cookies Secure en HTTP | El navegador no envía cookies | Usar `DEBUG=true` en local |
| Frontend no levantado | `AUT-E2E` no ejecuta | Iniciar Angular antes de Playwright |
| Datos residuales | Resultados inconsistentes | Base temporal de Django y comandos idempotentes |

## 9. Entregables

- Suite `AUT-BE` con cobertura.
- Suite `AUT-API` ejecutable por línea de comandos.
- Suite `AUT-E2E` con Playwright.
- Checklist `ACC`.
- Registro de ejecución y reporte de defectos.
