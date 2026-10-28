# Etapas de implementación — Beta 2.0.4

Documento de etapas de **Beta 2.0.4** (migración Pan pequeño → tabla `promociones` + FK `productos.promocion_id`, agrupación de carrito). Plan técnico: Context `docs/beta-2.0.4-promociones-plan.md`.

**Estado:** **cerrada** (etapas 0–7 en `main` vía #39–#44; OK final Daniel 2026-10-27). No quedan etapas pendientes.

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
| 0 | Alcance documentado (decisiones CLOSED) | Hecha | PRD/`stages`/regression en repo |
| 1 | Schema (`promociones` + `promocion_id`) | Hecha | [#39](https://github.com/Daniel-sanabria0419/system-bakery/pull/39) |
| 2 | Seed + backfill | Hecha | [#40](https://github.com/Daniel-sanabria0419/system-bakery/pull/40) |
| 3 | Dual-path / feature flag | Hecha | [#41](https://github.com/Daniel-sanabria0419/system-bakery/pull/41) |
| 4 | Recálculo carrito + UI subtotal/total | Hecha | [#42](https://github.com/Daniel-sanabria0419/system-bakery/pull/42) |
| 5 | Cutover | Hecha | [#43](https://github.com/Daniel-sanabria0419/system-bakery/pull/43) |
| 6 | Tests + regresión | Hecha | [#44](https://github.com/Daniel-sanabria0419/system-bakery/pull/44) — snapshot + huecos; suite offscreen |
| 7 | Pantallas / docs / nota reportes | Hecha | [#44](https://github.com/Daniel-sanabria0419/system-bakery/pull/44) — `regression-notes.md`; invariante `SUM(subtotal)` |

## Etapas 6–7 — Cierre (hecho en #44)

1. `schema_version` v3: `venta_lineas.id_promocion` + `nombre_promocion` (snapshot).
2. `register_sale` persiste refs/nombre de promo al confirmar.
3. Tests: snapshot estable tras rename/desactivar; 7 sola → 2000; mezcla promo + normal; migración v2→v3.
4. Docs: `docs/beta-2.0.4/regression-notes.md`, impacto pantallas, invariante reportes.
5. Criterio de cierre: cobro sin path por nombre de categoría; suite completa verde (**241 passed**).

## Fuera de alcance de Beta 2.0.4

CRUD rico de promociones en UI, otros `tipo` ≠ `cantidad_por_monto`, inventario, sync, login, reportes implementados, PostgreSQL, reabrir UX de Beta 2.0.3.

## Pruebas

Comando canónico: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`

Ver `docs/beta-2.0.4/regression-notes.md`.
