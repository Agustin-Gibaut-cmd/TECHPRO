# ACC — Checklist de aceptación manual

Ejecutar con backend y frontend levantados. Marcar `[x]` cuando el resultado
coincida con lo esperado y registrar evidencia en `testing/evidencias/`.

## Datos de acceso

| Rol | Email | Contraseña |
| --- | --- | --- |
| Administrador | `admin@techpro.local` | `TechproTest!2026` |
| Técnico | `tecnico@techpro.local` | `TechproTest!2026` |
| Vendedor | `vendedor@techpro.local` | `TechproTest!2026` |
| Consulta | `consulta@techpro.local` | `TechproTest!2026` |

## Checklist

| Caso | Verificación | Esperado | Estado |
| --- | --- | --- | --- |
| EF-01 | Abrir `http://127.0.0.1:8000/api/health/` | JSON `{"status":"ok"}` | [ ] |
| EF-02 | Registrarse con email nuevo y contraseña válida | Ingresa al dashboard | [ ] |
| EF-02 | Registrarse con contraseña corta | Mensaje de error, sin cuenta | [ ] |
| EF-03 | Iniciar sesión con `admin@techpro.local` | Ingresa al dashboard | [ ] |
| EF-03 | Recargar el dashboard | La sesión se mantiene | [ ] |
| EF-03 | Cerrar sesión | Vuelve al login | [ ] |
| EF-04 | Enviar login sin token CSRF (Postman/curl) | `403` | [ ] |
| EF-05 | Abrir `/api/repairs/` sin sesión | `401` | [ ] |
| EF-05 | Login como `consulta` e intentar crear un cliente | `403` | [ ] |
| EF-06 | Crear reparación con serial en minúsculas | Serial en mayúsculas | [ ] |
| EF-06 | Editar estado a “Listo” | Estado actualizado | [ ] |
| EF-06 | Eliminar reparación propia | Desaparece del listado | [ ] |
| EF-07 | Crear cliente con email inválido | Error de validación | [ ] |
| EF-07 | Crear, editar y eliminar cliente | Operaciones exitosas | [ ] |
| EF-08 | Crear, editar y eliminar proveedor | Operaciones exitosas | [ ] |
| EF-09 | Crear artículo con SKU en minúsculas | SKU en mayúsculas | [ ] |
| EF-09 | Repetir el mismo SKU | Error de duplicado | [ ] |
| EF-09 | Crear artículo con precio negativo | Error de validación | [ ] |
| EF-10 | Crear venta de 2 × 12500 | Total `25000.00` | [ ] |
| EF-10 | Editar cantidad a 3 | Total `37500.00` | [ ] |
| EF-10 | Crear venta con cantidad 0 | Error de validación | [ ] |
| EF-11 | Abrir reportes con datos propios | Métricas y gráficos coherentes | [ ] |
| EF-11 | Verificar que no aparezcan datos de otro usuario | Solo datos propios | [ ] |
| EF-12 | `PUT /api/repairs/` autenticado | `405` | [ ] |
| EF-12 | `POST /api/repairs/<id>/` autenticado | `405` | [ ] |

## Cierre

- Defectos encontrados:
- Evidencias adjuntas:
- Responsable:
- Fecha:
