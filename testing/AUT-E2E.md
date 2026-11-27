# AUT-E2E — Pruebas end-to-end con Playwright

## Requisitos

- Backend y frontend en ejecución.
- Usuarios de prueba creados.
- Node.js y npm.
- Navegador Chromium de Playwright.

## Preparación

Terminal 1 (backend):

```powershell
cd server
python manage.py migrate
python manage.py seed_test_users
python manage.py runserver 127.0.0.1:8000
```

Terminal 2 (frontend):

```powershell
cd client
npm install
npm start
```

Terminal 3 (E2E):

```powershell
cd testing/e2e
npm install
npx playwright install chromium
npm test
```

## Variables opcionales

| Variable | Valor por defecto |
| --- | --- |
| `TECHPRO_WEB_URL` | `http://127.0.0.1:4200` |
| `TECHPRO_TEST_EMAIL` | `admin@techpro.local` |
| `TECHPRO_TEST_PASSWORD` | `TechproTest!2026` |

## Casos cubiertos

1. Login con credenciales válidas y acceso a `/dashboard`.
2. Redirección a `/login` al intentar abrir `/dashboard` sin sesión.

## Evidencia

Playwright genera un reporte HTML en `testing/e2e/playwright-report/`. Guardá
una captura en `testing/evidencias/` si el examen lo requiere.
