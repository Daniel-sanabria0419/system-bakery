# Notas de regresión — Beta 2.0.2

## Suite

Comando:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest --import-mode=importlib
```

Al cierre de Etapa 6: **195 passed** (incl. smokes Beta 2 / 2.0.1 / 2.0.2).

## Adaptaciones / comportamientos intencionales

| Tema | Nota |
|---|---|
| Búsqueda por precio | UI `price_search_*` eliminada; dígitos sin selección filtran la grilla con `candidates_by_price_prefix` |
| Prefijo | Sobre el string del entero (`"4"` → 4500…); vacío = sin filtro de precio; categoría ∩ prefijo |
| Modos | Sin selección → prefijo; Pan pequeño → valor/ceil; otro producto → qty/`+/-` sin prefijo |
| Layout catálogo | `FlowLayout` por ancho; fondos sección `#d7d4ce`; divisor `catalog_sections_divider` |
| Panel seleccionado | Imagen / nombre / unitario + subtotal; orden qty → −/+ |
| Listado Productos | Fondo `#FFFFFF`; botones Editar/Activar siguen `payment-method-button` negro |
| Popup medios | Clase `payment-method-button` `#1A1A1A` intacta |

## Cobertura

| Área | Archivos principales |
|---|---|
| Prefijo app | `tests/test_beta202_price_prefix.py` |
| Prefijo UI / modos | `tests/test_beta201_desktop_sales.py`, `test_beta2_desktop_sales.py`, `test_beta2_smoke.py` |
| Wrap / fondos | `tests/test_beta201_catalog_chips.py` |
| Panel seleccionado | `tests/test_beta201_desktop_sales.py` |
| Listado blanco | `tests/test_beta2_desktop_products.py` |
| Smoke 2.0.2 | `tests/test_beta202_smoke.py` |
| Regresión 2.0.1 | `tests/test_beta201_*` |

## Sin regresiones de Beta 2.0.1

Se conservan Pan pequeño (promo 7/$2000), chips, imágenes, formularios Crear≈Editar, soft-delete y legado value-only.
