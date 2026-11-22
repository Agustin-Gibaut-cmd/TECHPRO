# TECHPRO

Aplicación con frontend Angular y API Django/PostgreSQL.

## Componentes

- [Frontend Angular](client/README.md): autenticación y módulo de reparaciones.
- [Backend Django](server/README.md): API REST de autenticación y reparaciones.
- [database.sql](database.sql): esquema SQL manual; para
  instalar el backend completo se deben usar las migraciones de Django.

## Seguridad antes de subir a GitHub

1. Verificá que `server/.env` y cualquier `.env` local estén ignorados:
   `git check-ignore -v server/.env`.
2. No agregues claves, contraseñas, tokens, dumps de datos ni certificados
   privados al repositorio. El `.env.example` usa marcadores intencionales.
3. Si una credencial real se subió alguna vez, ignorar el archivo no la borra
   del historial: rotala y limpiá el historial si corresponde.
4. Nunca pongas secretos en `client/src/environments/`; Angular los publica
   dentro del bundle.
5. Antes de producción, configurá las variables reales, `DEBUG=false`, TLS,
   hosts/orígenes explícitos y una cuenta PostgreSQL de privilegios mínimos.

## Configuración

El backend usa dotenv para cargar `server/.env`. El frontend no usa dotenv:
`environment.ts` y `environment.production.ts` son configuración pública de
Angular y se incluyen al compilar. El servidor SSR de Node recibe `PORT` desde
el entorno del proceso. Ver las guías de frontend y backend para detalles,
variables y riesgos conocidos.

## Capturas

<img width="1359" height="631" alt="image" src="https://github.com/user-attachments/assets/6489caf7-41eb-4e6c-b94e-c88e6ccfafb5" />
<img width="1359" height="633" alt="image" src="https://github.com/user-attachments/assets/0d11bef7-5d64-4395-bc75-da0bbe90e751" />
<img width="1359" height="626" alt="image" src="https://github.com/user-attachments/assets/797400c7-1e69-4708-a9ee-3ac2028cc866" />