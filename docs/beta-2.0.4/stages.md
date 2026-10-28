# Etapas de implementación — Beta 2.0.4

Documento de etapas de **Beta 2.0.4** (migración Pan pequeño → tabla `promociones` + FK `productos.promocion_id`, agrupación de carrito). Plan técnico: Context `docs/beta-2.0.4-promociones-plan.md`.

**Estado:** en curso (Etapa 1). Base: `main` post Beta 2.0.3 / P1 #38.

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
| 0 | Alcance documentado (decisiones CLOSED) | Hecha (plan Context) | PRD/`stages` en repo con Etapa 1 |
| 1 | Schema (`promociones` + `promocion_id`) | En revisión | [#39](https://github.com/Daniel-sanabria0419/system-bakery/pull/39); sin seed; sin cambio de cobro; sin columnas snapshot en `venta_lineas` |
| 2 | Seed + backfill | Pendiente | Promo + FK a productos Pan pequeño |
| 3 | Dual-path / feature flag | Pendiente | Flag off = cobro actual |
| 4 | Recálculo carrito + UI subtotal/total | Pendiente | **Obligatoria** |
| 5 | Cutover | Pendiente | Retirar path por nombre de categoría |
| 6 | Tests + regresión | Pendiente | Incl. 4+3 / 4+4 |
| 7 | Pantallas / docs / nota reportes | Pendiente | |

## Etapa 1 — Schema (alcance de este PR)

Sin cambiar cobro ni precios.

1. `CURRENT_SCHEMA_VERSION = 2`.
2. Tabla `promociones` (`id`, `nombre`, `tipo`, `configuracion` TEXT JSON, `activo`).
3. `productos.promocion_id` nullable FK a `promociones(id)` (ALTER idempotente).
4. DDL en `create_schema` para bases nuevas.
5. Repos mínimos + `promocion_id` expuesto en respuestas API de productos (aún sin usarlo en cobro).
6. Tests de migración idempotente / round-trip v1→v2.
7. **Sin seed** (Etapa 2). **Sin** columnas promo en `venta_lineas` (catálogo only; snapshot opcional en etapas posteriores).

## Fuera de alcance de Beta 2.0.4

CRUD rico de promociones en UI, otros `tipo` ≠ `cantidad_por_monto`, inventario, sync, login, reportes implementados, PostgreSQL, reabrir UX de Beta 2.0.3.

## Pruebas

Comando canónico: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`

Etapa 1: `tests/test_beta204_schema.py` (+ regresión de persistencia existente).
