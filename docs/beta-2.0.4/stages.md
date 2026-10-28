# Etapas de implementación — Beta 2.0.4

Documento de etapas de **Beta 2.0.4** (migración Pan pequeño → tabla `promociones` + FK `productos.promocion_id`, agrupación de carrito). Plan técnico: Context `docs/beta-2.0.4-promociones-plan.md`.

**Estado:** en curso (Etapa 2). Base: `main` con Etapa 1 mergeada (#39).

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
| 2 | Seed + backfill | En revisión | [#40](https://github.com/Daniel-sanabria0419/system-bakery/pull/40); promo canónica + FK a productos Pan pequeño; cobro sigue por nombre de categoría |
| 3 | Dual-path / feature flag | Pendiente | Flag off = cobro actual |
| 4 | Recálculo carrito + UI subtotal/total | Pendiente | **Obligatoria** |
| 5 | Cutover | Pendiente | Retirar path por nombre de categoría |
| 6 | Tests + regresión | Pendiente | Incl. 4+3 / 4+4 |
| 7 | Pantallas / docs / nota reportes | Pendiente | |

## Etapa 1 — Schema (hecha)

Sin cambiar cobro ni precios.

1. `CURRENT_SCHEMA_VERSION = 2`.
2. Tabla `promociones` (`id`, `nombre`, `tipo`, `configuracion` TEXT JSON, `activo`).
3. `productos.promocion_id` nullable FK a `promociones(id)` (ALTER idempotente).
4. DDL en `create_schema` para bases nuevas.
5. Repos mínimos + `promocion_id` expuesto en respuestas API de productos (aún sin usarlo en cobro).
6. Tests de migración idempotente / round-trip v1→v2.
7. Sin seed (Etapa 2). Sin columnas promo en `venta_lineas`.

## Etapa 2 — Seed + backfill (alcance de este PR)

Cobro **sigue** por nombre de categoría (`pan_pequeno_pricing`). Sin dual-path.

1. `ensure_promocion_pan_pequeno`: promo `cantidad_por_monto` con config `{precio_base: 300, grupo_cantidad: 7, grupo_monto: 2000, modo: ceil, politica_resto: todo_o_nada}`, `activo=1`.
2. `backfill_productos_promocion_pan_pequeno`: asigna `promocion_id` a todos los productos de categoría «Pan pequeño».
3. Ambos en `initialize` (idempotentes).
4. Tests FK / config / idempotencia (`tests/test_beta204_seed.py`).
5. **Sin** motor nuevo, flag ni cambio de precios en cobro.

## Fuera de alcance de Beta 2.0.4

CRUD rico de promociones en UI, otros `tipo` ≠ `cantidad_por_monto`, inventario, sync, login, reportes implementados, PostgreSQL, reabrir UX de Beta 2.0.3.

## Pruebas

Comando canónico: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`

Etapa 1: `tests/test_beta204_schema.py`. Etapa 2: `tests/test_beta204_seed.py`.
