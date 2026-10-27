# Notas de regresión — Beta 2.0.3

## Suite

Comando:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
```

Al cierre de Etapa 3: **202 passed** (incl. smokes Beta 2 / 2.0.1 / 2.0.2 / 2.0.3).

## Adaptaciones / comportamientos intencionales

| Tema | Nota |
|---|---|
| Vista A / B | Categorías y productos no se muestran a la vez; divisor oculto |
| Todos | En Vista A no usa estilo seleccionado |
| Volver catálogo | Chip `catalog_back_to_categories` en FlowLayout de productos; distinto de `back_button` (menú) |
| Prefijo | Sigue en Vista B como en 2.0.2 (categoría ∩ prefijo) |
| Chips | Tamaños/fuente desde `style.py`; QSS inyecta `*_FONT_SIZE` |
| Nombres largos | `CatalogChipButton` parte el texto en renglones |

## Cobertura

| Área | Archivos principales |
|---|---|
| Vista A/B | `tests/test_beta203_catalog_views.py` |
| Smoke 2.0.3 | `tests/test_beta203_smoke.py` |
| Chips / métricas / wrap | `tests/test_beta201_catalog_chips.py` |
| Regresión cobro 2.0.2 | `tests/test_beta202_smoke.py`, `test_beta201_desktop_sales.py` |
| Regresión 2.0.1 / 2.0 | `tests/test_beta201_*`, `test_beta2_*` |

## Sin regresiones de Beta 2.0.2 / 2.0.1

Se conservan prefijo, Pan pequeño, panel seleccionado, fondos `#d7d4ce`, listado Productos blanco, chips, imágenes, formularios, soft-delete y legado value-only.
