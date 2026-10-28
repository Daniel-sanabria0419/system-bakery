# Etapas de implementación — Beta 2.0.4

Documento de etapas de **Beta 2.0.4** (migración Pan pequeño → tabla `promociones` + FK `productos.promocion_id`, agrupación de carrito). Plan técnico: Context `docs/beta-2.0.4-promociones-plan.md`.

**Estado:** en curso (Etapa 5 cutover). Base: `main` con Etapas 1–4 mergeadas (#39–#42).

## Decisiones (resumen CLOSED)

| # | Tema | Decisión |
|---|---|---|
| 1 | Agrupación | Todo el carrito por `promocion_id` (tipo `cantidad_por_monto`, promo activa) |
| 2 | Resto | `todo_o_nada`: promo solo si `qty % grupo_cantidad == 0`; si no, `qty × precio_base` (8 → 2400) |
| 3 | UI cobro | Subtotal(es) de línea + total del carrito visibles y coherentes tras recálculo |
| 4 | Versión | **Beta 2.0.4** (no parche 2.0.3; no 2.1) |

## Estado de etapas

| Etapa | Nombre | Estado | Notas |
|---|---|---|---|
| 0 | Alcance documentado (decisiones CLOSED) | Hecha (plan Context) | PRD/`stages` en repo |
| 1 | Schema (`promociones` + `promocion_id`) | Hecha | [#39](https://github.com/Daniel-sanabria0419/system-bakery/pull/39) |
| 2 | Seed + backfill | Hecha | [#40](https://github.com/Daniel-sanabria0419/system-bakery/pull/40) |
| 3 | Dual-path / feature flag | Hecha | [#41](https://github.com/Daniel-sanabria0419/system-bakery/pull/41) |
| 4 | Recálculo carrito + UI subtotal/total | Hecha | [#42](https://github.com/Daniel-sanabria0419/system-bakery/pull/42) |
| 5 | Cutover | En revisión | [#43](https://github.com/Daniel-sanabria0419/system-bakery/pull/43); flag default True; sin montos por nombre de categoría en cobro |
| 6 | Tests + regresión | Pendiente | Incl. 4+3 / 4+4 |
| 7 | Pantallas / docs / nota reportes | Pendiente | |

## Etapa 5 — Cutover (alcance de este PR)

1. `USE_PROMOCIONES_TABLE = True` por defecto (apagable con `BAKERY_USE_PROMOCIONES_TABLE=0` → precio × cantidad plano).
2. Eliminado path de cobro por `is_pan_pequeno` / nombre de categoría en `SaleDraft` y `register_sale`.
3. `pan_pequeno_pricing` queda como **shim** (montos delegan a `promotions`; `is_pan_pequeno` solo catálogo/validación de lista).
4. Categoría «Pan pequeño» permanece; create/update asigna FK de promo canónica.
5. Invariante ingresos: `ventas.valor_total` = `SUM(venta_lineas.subtotal)` (no `precio × cantidad`).
6. Criterio: ningún path de cobro usa nombre de categoría para montos.

## Fuera de alcance de Beta 2.0.4

CRUD rico de promociones en UI, otros `tipo` ≠ `cantidad_por_monto`, inventario, sync, login, reportes implementados, PostgreSQL, reabrir UX de Beta 2.0.3.

## Pruebas

Comando canónico: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`

- Etapa 1–4: `tests/test_beta204_*.py`
- Cutover: suite completa + regresión Pan pequeño existente
