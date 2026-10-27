# Etapas de implementación — Beta 2.0.1

Documento de referencia de **Beta 2.0.1** (Pan pequeño, calculadora por valor, UI de catálogo/imágenes/formularios). Alcance autoritativo y plan detallado viven en el Context del proyecto (`beta-2.0.1-scope.md`, `beta-2.0.1-plan.md`).

**Estado:** etapas 1–8 en `main` (#19–#26); **Beta 2.0.1 cerrada** (OK final de Daniel, 2026-10-26).

Base: Beta 2.0 en `main` (productos + ventas con líneas).

## Decisiones (resumen)

| # | Tema | Decisión |
|---|---|---|
| 1 | Pan pequeño | Categoría por **nombre**; promo 7 / $2000 **solo en múltiplos exactos de 7**; unitario $300 |
| 2 | Precios | Módulo central `pan_pequeno_pricing` (ceil, enteros) |
| 3 | Calculadora | Por **valor** si categoría Pan pequeño; por unidades en el resto |
| 4 | UI cobro | Preview de redondeo antes de Agregar; `+/-` recalcula |
| 5 | Catálogo | Chips 93×70 / 87×60, `#64c466`; «Todos» primero |
| 6 | Imágenes | `ruta_imagen` en productos; dirs `imagenes/…`; categorías por convención |
| 7 | Formularios | Crear ≈ Editar; placeholder más oscuro que el fondo; texto negro |

## Estado de etapas

| Etapa | Nombre | Estado | PR |
|---|---|---|---|
| 0 | Análisis y diseño (Context) | Hecha | — |
| 1 | Semilla Pan pequeño + `ruta_imagen` | Hecha | #19 |
| 2 | Módulo precios Pan pequeño | Hecha | #20 |
| 3 | Compra / ventas con precios Pan pequeño | Hecha | #21 |
| 4 | UI cobro modo valor | Hecha | #22 |
| 5 | Chips catálogo + Todos | Hecha | #23 |
| 6 | Imágenes alta/edición/chips | Hecha | #24 |
| 7 | Estilo Crear / Editar | Hecha | #25 |
| 8 | Regresión + docs de cierre | Hecha; versión cerrada | #26 |

## Fuera de alcance

Motor genérico de promociones, `tiene_promocion` por producto, inventario, sync, login, reportes, IA, historial avanzado, Beta 2.1+.

## Pruebas

Comando: `QT_QPA_PLATFORM=offscreen python3 -m pytest`

Casos obligatorios: scope §§20–23 (ver `tests/test_beta201_*`). Smoke: `tests/test_beta201_smoke.py`. Notas: `docs/beta-2.0.1/regression-notes.md`.
