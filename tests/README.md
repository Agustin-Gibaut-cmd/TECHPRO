# Guía de Validación y Ejecución de Pruebas — TECHPRO

Este directorio centraliza la suite de comprobaciones y pruebas automatizadas de **TECHPRO**, cubriendo tanto el backend (Django / Django REST Framework) como el frontend (Angular).

---

## 1. Requisitos Previos

Antes de ejecutar las pruebas, asegurate de contar con el entorno configurado:

1. **Python 3.10 o superior** con las dependencias instaladas:
   ```powershell
   cd server
   python -m pip install -r requirements.txt
   ```
2. **Node.js (v18+) y npm** con las dependencias instaladas:
   ```powershell
   cd client
   npm install
   ```
3. **Base de Datos para Pruebas**:
   - **Opción recomendada (Rápida / Local):** Usar SQLite configurando `$env:DB_ENGINE = "sqlite"`. No requiere servidor de PostgreSQL activo.
   - **Opción PostgreSQL:** PostgreSQL en ejecución con un usuario con permisos para crear y destruir bases de datos temporales (`test_suite`).

---

## 2. Ejecución Automatizada Completa (`run-validation.ps1`)

El script `run-validation.ps1` ejecuta de forma secuencial todo el pipeline de aseguramiento de calidad del repositorio.

Desde la raíz del proyecto (`TECHPRO/`):

```powershell
.\tests\run-validation.ps1
```

> [!TIP]
> Si PowerShell bloquea la ejecución del script por políticas de seguridad del sistema, habilitá la ejecución temporal en la terminal actual:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\tests\run-validation.ps1
> ```

### Etapas que ejecuta el script:

| Etapa | Comando subyacente | Qué valida |
| :--- | :--- | :--- |
| **1. Django system check** | `python manage.py check` | Integridad de configuración, modelos, seguridad y claves en `server/`. |
| **2. Migration consistency** | `python manage.py makemigrations --check --dry-run` | Garantiza que no existan cambios de modelos sin su archivo de migración. |
| **3. Django API tests** | `python manage.py test tests` | Ejecuta las **75 pruebas** de integración y casos borde del backend. |
| **4. Angular component tests**| `npm test -- --watch=false` | Ejecuta las pruebas unitarias de componentes, guards y servicios del cliente. |
| **5. Angular production build**| `npm run build` | Compila la aplicación para producción asegurando cero errores de tipos TypeScript. |
| **6. Git whitespace check** | `git diff --check` | Detecta espacios en blanco o saltos de línea conflictivos en el repositorio. |

El script finaliza con **código de salida `0`** si todas las etapas resultan exitosas o **código `1`** indicando qué pasos fallaron.

---

## 3. Ejecución Manual por Módulos

Podés ejecutar pruebas individuales según el área de trabajo en la que estés realizando cambios:

### A. Backend (`server/`)

Ubicarse en el directorio `server`:

```powershell
cd server
```

#### 1. Ejecutar las 75 pruebas completas del backend:

Con SQLite (modo rápido, sin necesidad de PostgreSQL):
```powershell
$env:DB_ENGINE = "sqlite"
python manage.py test tests
```

Con PostgreSQL (según credenciales en `server/.env`):
```powershell
python manage.py test tests
```

#### 2. Ejecutar por paquete o dominio específico:

- **Configuración, Entorno y Seguridad:**
  ```powershell
  python manage.py test tests.config
  ```
  *Valida parsers de `.env`, auditoría de seguridad productiva, `/api/health/`, middleware anti-caché y constructor de base de datos.*

- **Autenticación y Sesiones:**
  ```powershell
  python manage.py test tests.accounts
  ```
  *Valida registro, contraseñas robustas, JWT en cookies HttpOnly, rotación, mitigación de replay attacks y rate limiting.*

- **Órdenes de Reparación:**
  ```powershell
  python manage.py test tests.repairs
  ```
  *Valida estados técnicos, límites de caracteres, validación de campos obligatorios, updates `PUT`/`PATCH` y aislamiento multitenant.*

- **Gestión de Taller, Stock, Ventas y Reportes:**
  ```powershell
  python manage.py test tests.workshop
  ```
  *Valida normalización de SKU, colisiones concurrentes de inventario, precisión decimal en ventas, clientes, proveedores y métricas continuas sin saltos.*

#### 3. Chequeos estáticos rápidos de Django:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

---

### B. Frontend (`client/`)

Ubicarse en el directorio `client`:

```powershell
cd client
```

#### 1. Pruebas de componentes (Karma / Jasmine):
```powershell
npm test -- --watch=false
```

#### 2. Comprobación de compilación y bundling:
```powershell
npm run build
```

---

## 4. Estructura de la Carpeta de Pruebas

```text
tests/
├── run-validation.ps1      # Orquestador automatizado para CI/CD y validación local
├── README.md               # Esta documentación técnica de ejecución
└── README.txt              # Resumen histórico en texto plano

server/tests/
├── config/                 # Pruebas de settings, base de datos, middleware y .env
│   ├── test_config.py
│   └── test_database.py
├── accounts/               # Pruebas de autenticación, JWT HttpOnly, CSRF y throttling
│   └── test_authentication.py
├── repairs/                # Pruebas de órdenes de servicio y ciclos de reparación
│   └── test_repairs_api.py
└── workshop/               # Pruebas de clientes, stock, proveedores, ventas y reportes
    └── test_workshop_api.py
```

---

## 5. Preguntas Frecuentes y Resolución de Problemas

- **Error de conexión a PostgreSQL (`port 5432 failed`):**
  Si estás validando en una máquina local sin el servicio PostgreSQL iniciado, seteá en tu terminal `$env:DB_ENGINE = "sqlite"`. El sistema correrá todas las pruebas automáticamente sobre SQLite en memoria/archivo temporal.
- **Error `ImproperlyConfigured` por Secret Keys:**
  Asegurate de que `server/.env` tenga definidas `DJANGO_SECRET_KEY` y `JWT_SIGNING_KEY` con al menos 50 caracteres cada una y que sean diferentes entre sí.
- **Pruebas sin alterar datos reales:**
  Django crea y destruye su propia base de datos temporal de pruebas (`test_...`). Ningún dato de desarrollo o producción se modifica durante la ejecución de los tests.
