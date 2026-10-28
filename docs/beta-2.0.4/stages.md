# Etapas de implementación — Beta 2.0.4

Documento de etapas de **Beta 2.0.4** (migración Pan pequeño → tabla `promociones` + FK `productos.promocion_id`, agrupación de carrito). Plan técnico: Context `docs/beta-2.0.4-promociones-plan.md`.

**Estado:** en curso (Etapa 4). Base: `main` con Etapas 1–3 mergeadas (#39–#41).

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
| 4 | Recálculo carrito + UI subtotal/total | En revisión | Lista/total UI + path activable (`BAKERY_USE_PROMOCIONES_TABLE` / flag); sin cutover |
| 5 | Cutover | Pendiente | Flag on por defecto; retirar path por nombre de categoría |
| 6 | Tests + regresión | Pendiente | Incl. 4+3 / 4+4 |
| 7 | Pantallas / docs / nota reportes | Pendiente | |

## Etapa 1 — Schema (hecha)

`schema_version` v2; tabla `promociones`; `productos.promocion_id`; repos/API; sin seed.

## Etapa 2 — Seed + backfill (hecha)

Promo canónica + backfill FK a productos «Pan pequeño».

## Etapa 3 — Dual-path / feature flag (hecha)

Motor `promotions` + `USE_PROMOCIONES_TABLE` default False; enrich API con flag on.

## Etapa 4 — Recálculo carrito + UI subtotal/total (alcance de este PR)

1. Tras Agregar/limpiar: subtotales de línea y **Total** reflejan agrupación (reparto B) cuando el path de promociones está activo.
2. `PurchaseLine.promocion_id` se conserva; subtotales de líneas previas pueden cambiar al cerrar combo.
3. UI (`register_sale_page`): lista `nombre × qty — subtotal`; pie `Total:`; panel de selección sigue mostrando subtotal preview pre-Agregar.
4. Path activable sin cutover: flag módulo o env `BAKERY_USE_PROMOCIONES_TABLE=1` (default sigue False hasta Etapa 5).
5. Tests desktop: 4+3 → total 2000 (subtotales suman 2000); 4+4 → 2400; espejo flag off → 2100.
6. Sin columnas snapshot en `venta_lineas` aún; sin retirar `pan_pequeno_pricing`.

## Fuera de alcance de Beta 2.0.4

CRUD rico de promociones en UI, otros `tipo` ≠ `cantidad_por_monto`, inventario, sync, login, reportes implementados, PostgreSQL, reabrir UX de Beta 2.0.3.

## Pruebas

Comando canónico: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`

- Etapa 1: `tests/test_beta204_schema.py`
- Etapa 2: `tests/test_beta204_seed.py`
- Etapa 3: `tests/test_beta204_promotions.py`
- Etapa 4: `tests/test_beta204_desktop_cart.py`
