# Notas de regresión — Beta 2.0.4

## Suite

Comando:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
```

Al cierre de Etapas 6–7: **241 passed** (incl. smokes 2.0–2.0.3 + `test_beta204_*`).

## Comportamientos intencionales

| Tema | Nota |
|---|---|
| Cobro | Montos por `productos.promocion_id` + motor `promotions` (no por nombre de categoría) |
| Agrupación | Todo el carrito por `promocion_id`; 4+3 → **2000**; 4+4 → **2400** |
| Resto | `todo_o_nada` (8 → 2400); `modo: ceil` solo valor→cantidad en el pad |
| Flag | `USE_PROMOCIONES_TABLE` default **True**; `BAKERY_USE_PROMOCIONES_TABLE=0` → precio × cantidad plano |
| Snapshot | `venta_lineas.id_promocion` / `nombre_promocion`; rename/desactivar promo no altera histórico |
| Invariante ingresos | `ventas.valor_total` = `SUM(venta_lineas.subtotal)` (no `precio × cantidad`) |
| Shim | `pan_pequeno_pricing` delega montos a `promotions`; `is_pan_pequeno` solo catálogo/validación de lista |
| UI | Lista `nombre × qty — subtotal` + `Total` post-grupo; panel selección = preview pre-Agregar |
| Vista A/B | Sin cambio estructural (2.0.3 intacta) |

## Cobertura

| Área | Archivos principales |
|---|---|
| Schema / seed | `tests/test_beta204_schema.py`, `test_beta204_seed.py` |
| Motor / dual-path | `tests/test_beta204_promotions.py` |
| UI carrito | `tests/test_beta204_desktop_cart.py` |
| Snapshot / cierre | `tests/test_beta204_closure.py` |
| Regresión cobro previa | `tests/test_beta201_*`, `test_beta202_smoke.py`, `test_beta203_*` |

## Pantallas (Etapa 7)

| Superficie | Impacto |
|---|---|
| Registrar venta | Pad valor si promo activa; subtotales/total agrupados; confirmación usa total de grupo |
| Productos CRUD | create/update en Pan pequeño asigna FK; lectura de promo en API; CRUD rico de promos diferido |
| Menú / Vista A-B | Sin cambio |
| Medios / diálogos | Confirman el total ya agrupado |
| Reportes | N/A; invariante `SUM(subtotal)` documentado |

## Sin regresiones de Beta 2.0.3 / 2.0.2 / 2.0.1

Se conservan Vista A/B, prefijo, chips, panel seleccionado, fondos, listado Productos blanco, imágenes, formularios, soft-delete y legado value-only.
