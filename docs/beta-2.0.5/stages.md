# Etapas de implementación — Beta 2.0.5

**Estado:** en curso (motor híbrido). Base: `main` post Beta 2.0.4 (#39–#45).

Diseño CLOSED: Context `docs/beta-2.0.5-promo-por-producto-y-grupo.md`.

## Decisiones (CLOSED)

| # | Tema | Decisión |
|---|---|---|
| A | Capa 1 | Múltiplos **exactos** por `id_producto` (no greedy; 8 → 2400) |
| B | Unidad | Agregar qty por **`id_producto`** |
| C | Capa 2 | Pool no-exactos + `todo_o_nada` (4+3 → 2000; 10+4 → 4000) |
| D | Versión | **Beta 2.0.5** |
| E | Pad | Preview selección como 2.0.4; total tras Agregar |

## Estado de etapas

| Etapa | Nombre | Estado | Notas |
|---|---|---|---|
| 0 | Diseño CLOSED | Hecha | Context diseño + OK Daniel |
| 1 | Motor híbrido + tests + docs | En revisión | `promotions.amount_for_cart_group`; suite |

## Alcance Etapa 1

1. `amount_for_cart_group` / `compute_cart_line_subtotals` híbridos; callers pasan `id_producto`.
2. Tests: 7+5→3500, 4+3→2000, 8→2400, 10+4→4000, agregación mismo SKU.
3. Docs: AGENTS / PRD / este `stages.md`.
4. Sin schema nuevo; pad/preview sin cambio.

## Fuera de alcance

CRUD promos, otros `tipo`, inventario, sync, login, reportes, Beta 2.1+.

## Pruebas

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
```
