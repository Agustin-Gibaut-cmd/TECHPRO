# Testing

- `api/`: smoke tests HTTP contra un backend en ejecución.
- `e2e/`: pruebas end-to-end con Playwright.
- `evidencias/`: evidencias y reportes de accesibilidad.

Ejecución:
- API: `python -m unittest discover -s testing/api`
- E2E: `npm test` dentro de `testing/e2e`
