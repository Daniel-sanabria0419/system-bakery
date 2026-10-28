# Etapas de implementación — Beta 2.0.5

**Estado:** cobro greedy packs (reemplaza `todo_o_nada`). Base: `main` post Beta 2.0.4 / 2.0.6 UI.

## Decisiones vigentes

| # | Tema | Decisión |
|---|---|---|
| A | Cobro | Packs greedy: `(qty // G) * M + (qty % G) * P` (8 → 2300; 17 → 4900) |
| B | Carrito | Suma qty del mismo `promocion_id` + misma fórmula (4+3 → 2000; 7+5 → 3500) |
| C | Config | `precio_base`, `grupo_cantidad`, `grupo_monto`, `modo: ceil` — sin `politica_resto` / `ajuste_manual` |
| D | Pad | `modo: ceil` = valor→qty; cobro greedy de esa qty |

## Ejemplos (G=7, M=2000, P=300)

| Qty / carrito | Monto |
|---|---|
| 7 | 2000 |
| 8 | 2300 |
| 14 | 4000 |
| 17 | 4900 |
| 4+3 | 2000 |
| 7+5 | 3500 |

## Pruebas

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
```
