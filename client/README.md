# Frontend Angular

## Desarrollo local

Requiere Node.js y npm. Desde `client`:

```powershell
npm install
npm start
```

La app queda en `http://localhost:4200`. El entorno de desarrollo usa
`src/environments/environment.ts` y conecta al backend local
`http://localhost:8000/api`. Levantá Django siguiendo [server/README.md](../server/README.md).

## Configuración y secretos

Angular no carga `server/.env` ni debe recibir secretos del backend. Los valores
de `src/environments/` se compilan dentro de JavaScript y cualquier usuario
puede inspeccionarlos. Allí solo va información pública, como la URL del API.
Desarrollo usa HTTP solo contra `localhost`. Producción usa la ruta `/api` del
mismo origen; el proxy HTTPS debe reenviarla al backend. Los archivos contienen
solo configuración pública; no agregues tokens ni secretos.

La build de producción reemplaza el entorno local por
`src/environments/environment.production.ts`, configurado para usar `/api` en
el mismo origen. El servidor/proxy de producción debe servir el frontend por
HTTPS y reenviar `/api` a Django. Si el API usa otro dominio, modificá `apiUrl`
antes de compilar y permití ese origen exacto en `CORS_ALLOWED_ORIGINS`.

El servidor SSR de Node usa `PORT` (por defecto `4000`) y `HOST` (por defecto
`127.0.0.1`) del entorno del proceso; no carga dotenv. En contenedores
configurá `HOST=0.0.0.0` explícitamente. Node agrega headers de seguridad y
responde con un error genérico si falla el render SSR.

## Autenticación y punto frágil

`AuthService` maneja login, registro, refresh y logout. Access y refresh viajan
en cookies `HttpOnly`; el JavaScript no puede leerlos. El token CSRF se obtiene
del backend y se mantiene solo en memoria. El guard de rutas mejora la
navegación, pero la autorización real siempre debe quedar en Django. Una
vulnerabilidad XSS aún podría enviar solicitudes como el usuario; mantené
sanitización y una política CSP adecuada en el proxy.

Las secciones **Reparaciones**, **Clientes** e **Inventario** tienen formularios
y tablas conectadas al API autenticado. Cada usuario solo consulta y modifica
sus propios registros; el inventario valida SKU único por cuenta y cantidades
y precios no negativos.

## Verificación

```powershell
npm run build
npm test
```

La guía general, variables y lista de comprobación para GitHub están en
[README.md](../README.md).
