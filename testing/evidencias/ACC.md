<!--
Bloque listo para copiar y pegar.
Cierre del criterio de accesibilidad WCAG 2.2 AA — TECHPRO.
-->

# ACC — Auditoría de Accesibilidad WCAG 2.2 AA

## Cierre del criterio

| Campo | Valor |
| --- | --- |
| Criterio | Auditoría WCAG 2.2 AA realizada y hallazgos corregidos y documentados |
| Requisito | "Como usuario con necesidades de accesibilidad, quiero navegar la interfaz bajo criterios WCAG 2.2 AA, para usar el sistema sin barreras visuales o de teclado." |
| Norma aplicada | WCAG 2.2, nivel AA (W3C) |
| Alcance | Frontend Angular + Tailwind en `client/` (login `auth-form`, navegación `dashboard`, formularios, botones, confirmaciones inline de borrado, estados de error, estados de carga, contraste, semántica y ARIA, estilos globales `styles.css`, `index.html`) |
| Fuera de alcance | Backend Django REST (`server/`), integración E2E (cerrada aparte), funcionalidad de negocio no relacionada con accesibilidad |
| Metodología | Revisión manual de vistas/componentes/estilos; verificación de semántica HTML y ARIA; cálculo de contraste WCAG sobre la paleta real (4.5:1 texto / 3:1 componentes y texto grande); revisión de orden de foco, operabilidad por teclado (Tab / Shift+Tab / Enter / Escape), `focus-visible`, tamaño de objetivo, idioma y título de página; `ng build` + `ng test`; inspección del HTML renderizado (SSR); auditoría Lighthouse Accessibility en navegador |
| Resultado | **Cumple WCAG 2.2 AA** — hallazgos corregidos y documentados (ver tabla). Sin dependencias nuevas; sin cambios de funcionalidad fuera de accesibilidad; E2E no reabierto |
| Fecha | 2026-11-27 |
| Responsable | Fabricio Agustín Gibaut Carrizo |
| Estado | **Cerrado / Aprobado** |

---

## Resumen ejecutivo

Se realizó auditoría de accesibilidad bajo WCAG 2.2 nivel AA sobre todo el frontend
(`client/`). Se detectaron hallazgos en **foco visible**, **contraste no textual**,
**asociación de etiquetas y errores**, **estado de componentes ARIA**, **anuncio de
mensajes de estado**, **orden/gestión de foco**, **tamaño de objetivo**,
**título de página** y **movimiento reducido**. Todos los hallazgos fueron corregidos
con cambios mínimos y limpios. Se verificó que el **contraste de texto (1.4.3) ya
cumplía 4.5:1** (4.5:1 normal / 3:1 texto grande) en toda la paleta. No se introdujo
ninguna funcionalidad nueva ni dependencia. `npm run build` y `ng test` se ejecutan
(ver "Verificación"). Queda como recomendación opcional una validación complementaria
con lector de pantalla (NVDA/VoiceOver) y `axe-core` en CI; no es requisito del
cierre de este criterio.

---

## Hallazgos detectados y corregidos

| # | Hallazgo | Criterio WCAG 2.2 AA | Nivel | Archivo(s) | Corrección aplicada | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| H-01 | `outline-none` / `focus:outline-none` suprimía el indicador de foco en login, formularios y tarjetas; no había `focus-visible`. | 2.4.7 Focus Visible | AA | `styles.css`, `auth-form.html`, `customers.html`, `inventory.html`, `repairs.html`, `suppliers.html`, `sales.html`, `dashboard.html` | Regla global `:focus-visible { outline: 2px solid #9AF3C7; outline-offset: 2px; }` (contraste ≈12–14:1) + `:focus:not(:focus-visible){ outline:none; }`; se removieron las clases que apagaban el `outline`. | Corregido |
| H-02 | En login `focus:border-[#33434F]` con contraste ~1.6:1 sobre `#172129`; en textareas `focus:border-[#737373]`. | 1.4.11 Non-text Contrast; 2.4.7 Focus Visible | AA | `auth-form.html`, `repairs.html`, `customers.html`, `inventory.html`, `suppliers.html`, `sales.html` | Foco por `focus:border-[#9AF3C7]` + `outline` `#9AF3C7` ≥3:1; no se oculta el foco. | Corregido |
| H-03 | Contraste no textual insuficiente de bordes: `#33434F` ~1.6–1.8:1, `#383838` ~1.5:1, borde transparente de inputs en login, `border-red-900/70` ~1.33, `border-emerald-900/70` ~1.41, `border-red-500/60` ~2.28, divisores de tabla. | 1.4.11 Non-text Contrast | AA | todos los módulos + `dashboard.html` + `auth-form.html` | Paleta accesible `#5A7085` (≥3.18:1 sobre `#0C1218`/`#172129`/`#171717`); `border-red-400`, `border-emerald-400`, `border-[#9AF3C7]`, `border-[#5A7085]`, `divide-[#5A7085]`. | Corregido |
| H-04 | Uso de color sin duplicar sentido en gráficos/estados; barra `#2E7D6B` ~3.31:1. | 1.4.11 Non-text Contrast; 1.4.1 Use of Color | AA | `reports.html`, `inventory.html`, `auth-form.html` | ≥3:1 conservado; información también por texto/`<title>`/`aria-*`. | Verificado |
| H-05 | Campos con error no exponían `aria-invalid`. | 4.1.2 Name, Role, Value | A | `auth-form.html`, `customers.html`, `inventory.html`, `repairs.html`, `suppliers.html`, `sales.html` | `[attr.aria-invalid]` ligado a `touched && invalid` (+ `passwordMismatch` en `confirmPassword`). | Corregido |
| H-06 | Mensajes de error no asociados al campo; error anidado dentro de `<label>`. | 1.3.1 Info and Relationships; 3.3.1 Error Identification; 4.1.2 Name, Role, Value | A | `auth-form.html`, `customers.html`, `inventory.html`, `repairs.html`, `suppliers.html`, `sales.html` | `id` por campo + `[attr.aria-describedby]` al `id` del mensaje; mensaje fuera del `<label>`; `role="alert"`. | Corregido |
| H-07 | Login sin `<label>` visible (solo `aria-label` + `placeholder`); `placeholder` no sustituye etiqueta. | 3.3.2 Labels or Instructions; 1.3.1 Info and Relationships | A | `auth-form.html` | `<label for>` visible + `id`; se conserva `placeholder`; `aria-label` redundante removido. | Corregido |
| H-08 | Campos obligatorios marcados solo con `*` visual; sin estado programático. | 3.3.2 Labels or Instructions; 4.1.2 Name, Role, Value | A | `auth-form.html`, `customers.html`, `inventory.html`, `repairs.html`, `suppliers.html`, `sales.html` | `aria-required="true"`; texto "Los campos marcados con * son obligatorios." / "obligatorios". | Corregido |
| H-09 | Mensajes de error/éxito/carga no anunciados; sin `aria-live`. | 4.1.3 Status Messages; 3.3.1 Error Identification | AA | `auth-form.html`, `customers.html`, `inventory.html`, `repairs.html`, `suppliers.html`, `sales.html`, `dashboard.html`, `reports.html` | `role="alert"`, `role="status"`, `aria-live="polite"` (total de venta), `role="status"` en cargas, `[attr.aria-busy]`. | Corregido |
| H-10 | Toggles "Ver/Ocultar contraseña" sin estado expuesto. | 4.1.2 Name, Role, Value | A | `auth-form.html` | `aria-pressed`, `aria-label` dinámico, `aria-hidden` en SVG. | Corregido |
| H-11 | Elementos decorativos SVG sin `aria-hidden`. | 1.1.1 Non-text Content; 4.1.2 Name, Role, Value | A | `auth-form.html`, `dashboard.html`, `reports.html` | `aria-hidden="true"`; gráficos `role="img"` + `aria-label` + `<title>`. | Corregido |
| H-12 | Sin salida por `Escape` en confirmación inline de borrado. | 2.1.1 Keyboard; 2.1.2 No Keyboard Trap | A | `customers.html`, `inventory.html`, `repairs.html`, `suppliers.html`, `sales.html` | `(keydown.escape)` cancela la confirmación; se mantiene botón "Cancelar". (No hay modales/`dialog`; no hay trampa de foco.) | Corregido |
| H-13 | Foco perdido al abrir/cerrar módulo (elemento enfocado removido del DOM). | 2.4.3 Focus Order; 2.4.7 Focus Visible | A / AA | `dashboard.html`, `dashboard.ts` | Gestión de foco: `tabindex="-1"` + foco a `#module-content` al abrir y restauración a la tarjeta al volver. | Corregido |
| H-14 | Objetivos táctiles pequeños (toggle de contraseña 24px; botón de modo sin relleno). | 2.5.8 Target Size (Minimum) | AA | `auth-form.html` | `p-1`→`p-1.5`; `py-1.5 px-2`. Todo objetivo ≥24×24 px CSS. | Corregido |
| H-15 | Título de página único sin distinguir vista. | 2.4.2 Page Titled | A | `app.ts`, `index.html` | `Title` por ruta (`Iniciar sesión · TECHPRO` / `Panel · TECHPRO`); `lang="es"`. | Corregido |
| H-16 | Animaciones/transiciones sin respetar preferencia de reducir movimiento. | 2.3.3 Animation from Interactions; 2.2.2 Pause, Stop, Hide | AAA / A | `styles.css` | `@media (prefers-reduced-motion: reduce)`. | Corregido |
| H-17 | Foco no obstruido. | 2.4.11 Focus Not Obscured (Minimum) | AA | — | Verificado: sin elementos sticky/solapados; `outline-offset`. | Verificado |

---

## Criterios verificados sin cambios (ya cumplían)

| Criterio WCAG 2.2 AA | Verificación |
| --- | --- |
| 1.4.3 Contrast (Minimum) AA | Toda la paleta de texto cumple 4.5:1 (normal) / 3:1 (grande): `#F1F6F8` 15–17:1, `#AFBDC7` 8.5–9.8:1, `#c7c7c7` ~9.7–11:1, `#ededed` 15.3:1, `#9AF3C7` 12–14:1, `#0C1218` sobre `#9AF3C7` 14.4:1, `#9AF3C7` sobre `#7FD8AA`, `text-red-400` ~5.9–6.8:1, `text-red-300` ~8.9–9.8:1, `text-emerald-300` ~10.5–11.7:1, `amber-300` ~9.5–13:1. (Los controles deshabilitados quedan exentos.) |
| 1.4.1 Use of Color A | La información no se transmite solo por color: texto + icono/etiqueta; error siempre con mensaje; "Stock bajo" con texto; "mes actual" con etiqueta; `aria-*`. |
| 1.3.1 Info and Relationships A | Semántica: `<main>`, `<header>`, `<section>`, `<form>`, `<label>`, `<h1>`→`<h2>`→`<h3>`, `<table>` + `<th scope="col">`, listas, `role`. |
| 1.3.2 Meaningful Sequence A | Orden de lectura = orden de DOM; sin `float`/reordenamiento que rompa sentido. |
| 1.3.5 Identify Input Purpose AA | `autocomplete` (`email`, `name`, `tel`, `current-password`, `new-password`, `street-address`, `organization`, `off`). |
| 2.1.1 Keyboard A | Todo operable por teclado con controles nativos; sin handlers solo de mouse. |
| 2.1.2 No Keyboard Trap A | Sin trampa de foco; `tabindex` solo `-1`. |
| 2.4.1 Bypass Blocks A | Sin bloques repetidos que requieran saltar; `<main>`. |
| 2.4.2 Page Titled A | `<title>` + por ruta (ver H-15). |
| 2.4.3 Focus Order A | Orden lógico; sin `tabindex>0`; gestión de foco (ver H-13). |
| 2.4.6 Headings and Labels AA | Jerarquía de encabezados; etiquetas descriptivas. |
| 2.4.7 Focus Visible AA | Foco visible `:focus-visible`. |
| 2.4.11 Focus Not Obscured (Minimum) AA | Foco no oculto; `outline-offset`. |
| 2.5.8 Target Size (Minimum) AA | Objetivos ≥24×24 px CSS (ver H-14). |
| 2.5.7 Dragging Movements AA | No hay interacción de arrastre. |
| 3.1.1 Language of Page A | `<html lang="es">`. |
| 3.2.1 On Focus A / 3.2.2 On Input A | Sin cambios de contexto inesperados al enfocar o escribir. |
| 3.2.6 Consistent Help AA | Sin mecanismos de ayuda inconsistentes. |
| 3.3.3 Error Suggestion AA | Mensajes con sugerencia de corrección. |
| 3.3.7 Redundant Entry AA | No se exige re-escribir datos previos; `autocomplete`. La repetición de contraseña (`confirmPassword`) es verificación de seguridad/exactitud y no bloquea copiar/pegar ni autocompletar. |
| 3.3.8 Accessible Authentication (Minimum) AA | Sin CAPTCHA ni prueba cognitiva; se permite pegar; `autocomplete`; mostrar/ocultar contraseña; no se bloquea gestor de contraseñas. |
| 4.1.2 Name, Role, Value A | Nombre/rol/valor nativos + ARIA (`aria-*`). |
| 4.1.3 Status Messages AA | `role="alert"`, `role="status"`, `aria-live`. |

---

## Verificación (comandos)

```bash
cd client
npm run build      # ng build → OK
npm test           # ng test  → ver nota abajo
```

### Nota de honestidad / no regresión

- `npm run build`: **OK**.
- `ng test`: **32/33**. Falla 1 test **pre-existente en `main` sin relación con accesibilidad**:
  `auth-form.spec.ts > AuthForm > validates registration credentials and matching passwords`
  (`authForm.hasError('passwordMismatch')` esperado `true`). Reproducible en `main`
  limpio antes de estos cambios; **no** fue introducido ni modificado por la auditoría
  WCAG 2.2 AA. No se tocó lógica de validación. (No se reabre la integración E2E.)
- Contraste calculado sobre la paleta real con fórmula WCAG (luminancia relativa sRGB).
- Verificación en navegador (OpenCode in-app browser):
  - **Lighthouse Accessibility = 100/100**; Best Practices = 100/100. (Solo fallan ítems de SEO no relacionados: `meta-description`, `robots.txt`.)
  - Árbol de accesibilidad expone nombre/rol/`required`/`invalid`/`pressed`; `lang="es"`; título de página por ruta.
  - `:focus-visible` computado: `outline: rgb(154,243,199) solid 2px; outline-offset: 2px`.
  - Operabilidad por teclado (Tab / Shift+Tab / Enter); controles nativos; sin trampa de foco; `Escape` en confirmación inline; gestión de foco.
  - **No se añade ninguna dependencia** (no `axe-core`); auditoría WCAG 2.2 AA manual + cálculo de contraste + Lighthouse.
- Sin nuevas dependencias; sin cambios en `server/`; sin cambios fuera de accesibilidad.

## Archivos modificados (solo accesibilidad, `client/`)

- `client/src/styles.css` — foco `:focus-visible`, `:focus:not(:focus-visible)`, `prefers-reduced-motion`.
- `client/src/app/auth-form/auth-form.html` — etiquetas, `aria-*`, errores, `aria-pressed`, `aria-busy`, `aria-hidden`, foco.
- `client/src/app/dashboard/dashboard.html` — bordes accesibles, `focus-visible`, `id`, `tabindex="-1"`, `<main id>`.
- `client/src/app/dashboard/dashboard.ts` — gestión de foco al abrir/cerrar módulo.
- `client/src/app/customers/customers.html` — etiquetas, `aria-*`, errores, `aria-busy`, Escape, bordes.
- `client/src/app/inventory/inventory.html` — ídem.
- `client/src/app/repairs/repairs.html` — ídem.
- `client/src/app/suppliers/suppliers.html` — ídem.
- `client/src/app/sales/sales.html` — ídem + `aria-live` en total.
- `client/src/app/reports/reports.html` — bordes accesibles, `role="status"` carga.
- `client/src/app/app.ts` — título de página por ruta (WCAG 2.4.2).

## Cierre

- Defectos encontrados (accesibilidad): **17** (H-01…H-17).
- Defectos corregidos por accesibilidad: **15** (H-01…H-03, H-05…H-16). Verificados sin cambios: **H-04, H-17** + lista "Criterios verificados sin cambios". Defectos abiertos por accesibilidad: **0**.
- Defecto no relacionado (no accesibilidad, pre-existente en `main`): 1 test unitario `passwordMismatch`. No bloquea este criterio.
- Evidencias adjuntas: este documento `testing/evidencias/ACC.md`.
- Responsable: Fabricio Agustín Gibaut Carrizo
- Fecha: 2026-11-27
- Estado: **Cerrado / Aprobado**
