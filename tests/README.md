# Validación integral — TECHPRO

Este directorio conserva el script de validación. La documentación de pruebas,
los casos `EF-01` a `EF-12` y las suites `AUT-API`, `AUT-E2E` y `ACC` están en
[`testing/Testing.md`](../testing/Testing.md).

## Ejecución rápida

```powershell
# Backend con cobertura
cd server
coverage run --branch manage.py test
coverage report -m

# Contrato HTTP (backend levantado)
python -m unittest discover -s testing/api -v

# End-to-end (backend y frontend levantados)
cd testing/e2e
npm test

# Aceptación manual
# Seguir testing/ACC.md
```

## Script completo

```powershell
.\tests\run-validation.ps1
```

El script ejecuta:

1. `manage.py check`.
2. `makemigrations --check --dry-run`.
3. Suite backend con `coverage` (o `manage.py test` si coverage no está instalado).
4. Pruebas de Angular y build de producción.
5. `git diff --check`.

Si PowerShell bloquea el script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\tests\run-validation.ps1
```
