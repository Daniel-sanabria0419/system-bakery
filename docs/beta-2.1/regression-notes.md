# Notas de regresión — Beta 2.1 (Etapa 9)

## Suite

Comando canónico:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
```

Al cierre de Etapa 9: **364 passed** (incl. smokes 2.0–2.0.x, #61–#66 y `test_beta21_*`).

## Ventana de edición (definición inclusive)

| Regla | Valor |
|---|---|
| Constante | `EDITABLE_WINDOW_SECONDS = 3600` |
| Criterio | `editable` **solo si** `elapsed < 3600` segundos desde `fecha_venta` |
| Borde exacto | `elapsed == 3600` → **no** editable (`SaleNotEditableError` / HTTP 409) |
| Reloj | Solo proceso API local; UI countdown informativo |

## Bordes cubiertos en Etapa 9

| Caso | Dónde |
|---|---|
| Legado value-only (listado/detalle, sin inventar líneas) | `tests/test_beta21_regresion_etapa9.py`, etapas 2–6 |
| Ventana exacta `< 3600` | `test_beta21_regresion_etapa9`, `test_beta21_persistencia_etapa2`, `test_beta21_edicion_etapa6` |
| Carrera / reintento POST mismo UUID | `test_register_sale_integrity_race_returns_existing`, `test_sale_idempotency` |
| Menú Historial + cobro intacto | `test_post_create_still_works_with_historial_menu` |

## Checklist regresión cobro / catálogo / productos

| # | Tema | Estado | Evidencia principal |
|---|---|---|---|
| 61 | `subtotal` (lista) + `total` (cobrado) por línea | OK | `test_venta_lineas_total`, `test_beta21_regresion_etapa9` |
| 62 | Snapshot promo solo si hubo descuento | OK | `test_beta201_sales_pricing`, regresión etapa 9 |
| 63 | `precio_aplicado` = precio de lista vigente | OK | rechazo mismatch en API; regresión etapa 9 |
| 64 | Revalidar carrito al volver / pagar | OK | `test_cart_revalidate_*`, regresión etapa 9 |
| 65 | Idempotencia `POST /ventas` (UUID cliente) | OK | `test_sale_idempotency` + carrera IntegrityError |
| 66 | `ensure_imagenes_dirs` en `initialize` | OK | `test_beta201_product_images`, regresión etapa 9 |
| — | Promo por línea (nudos / ceil) | OK | `test_beta205_*`, `test_beta206_*`, `test_beta204_*` |
| — | CRUD productos / soft-delete / snapshot | OK | `test_beta2_api_products`, `test_beta2_integrity` |
| — | Prefijo precio / Vista A-B / chips | OK | `test_beta202_*`, `test_beta203_*` |
| — | Historial / detalle / obs / PUT / auditoría / UI edit | OK | `test_beta21_*` etapas 1–8 |

## Comportamientos intencionales de Beta 2.1 (no son regresiones 2.0.x)

| Tema | Nota |
|---|---|
| Schema | `schema_version` v6: `venta_observaciones`, `venta_cambios` |
| Lectura | `GET /ventas`, `GET /ventas/{id}`, `GET /ventas/{id}/cambios` |
| Obs | `observacion` opcional en POST; `POST /ventas/{id}/observaciones` siempre |
| Edición | `PUT /ventas/{id}` solo dentro de ventana; recalc promo vigente |
| Legado | Historial/detalle sí; no inventar `venta_lineas` |
| Menú | Tercer botón **Historial**; Registrar venta y Productos intactos |
| `POST /ventas` | Sigue idempotente; no se reutiliza para mutar |

## Sin regresiones de Beta 2.0.x

Se conservan: enteros (sin float dinero), snapshot de líneas, promo por línea, UUID cliente + idempotencia, revalidación de carrito, precio de lista, snapshot promo solo con descuento, `ensure_imagenes_dirs`, catálogo/Vista A-B/prefijo, soft-delete, y legado value-only.
