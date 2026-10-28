# Etapas de implementación — Beta 2.0.4

Documento de etapas de **Beta 2.0.4** (migración Pan pequeño → tabla `promociones` + FK `productos.promocion_id`, agrupación de carrito). Plan técnico: Context `docs/beta-2.0.4-promociones-plan.md`.

**Estado:** en curso (Etapa 3). Base: `main` con Etapas 1–2 mergeadas (#39, #40).

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
| 3 | Dual-path / feature flag | En revisión | [#41](https://github.com/Daniel-sanabria0419/system-bakery/pull/41); motor `promotions` + flag `USE_PROMOCIONES_TABLE` default False |
| 4 | Recálculo carrito + UI subtotal/total | Pendiente | **Obligatoria** (pulido UI; motor ya agrupa con flag on) |
| 5 | Cutover | Pendiente | Retirar path por nombre de categoría |
| 6 | Tests + regresión | Pendiente | Incl. 4+3 / 4+4 |
| 7 | Pantallas / docs / nota reportes | Pendiente | |

## Etapa 1 — Schema (hecha)

`schema_version` v2; tabla `promociones`; `productos.promocion_id`; repos/API; sin seed.

## Etapa 2 — Seed + backfill (hecha)

Promo canónica + backfill FK a productos «Pan pequeño». Cobro por nombre de categoría.

## Etapa 3 — Dual-path / feature flag (alcance de este PR)

1. Módulo `bakery/app/promotions.py`: fórmula §4.1, `quantity_from_value`, `amount_for_cart_group`, reparto B, `compute_cart_line_subtotals`.
2. Paridad unitaria vs montos 2.0.1 (6/7/8/14, 1900→7/2000).
3. Flag `USE_PROMOCIONES_TABLE` default **False**:
   - off → path actual (`pan_pequeno_pricing`, promo por línea; 4+3 = 2100).
   - on → FK + motor + **agrupación carrito** (4+3 = 2000) en `SaleDraft` y `register_sale`.
4. Enrich API/productos con `promocion_tipo` / `promocion_configuracion` / `promocion_activo` solo con flag on.
5. Suite espejo on/off (`tests/test_beta204_promotions.py`).
6. **Sin cutover**; flujo de venta seguro con flag off.

## Fuera de alcance de Beta 2.0.4

CRUD rico de promociones en UI, otros `tipo` ≠ `cantidad_por_monto`, inventario, sync, login, reportes implementados, PostgreSQL, reabrir UX de Beta 2.0.3.

## Pruebas

Comando canónico: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`

- Etapa 1: `tests/test_beta204_schema.py`
- Etapa 2: `tests/test_beta204_seed.py`
- Etapa 3: `tests/test_beta204_promotions.py`
