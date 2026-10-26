# Notas de regresión — Beta 2.0.1

## Suite

Comando:

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest
```

Al cierre de Etapa 8: **178 passed** (incl. smoke Beta 2 y Beta 2.0.1).

## Adaptaciones / comportamientos intencionales

| Tema | Nota |
|---|---|
| Pan pequeño | Subtotal vía `pan_pequeno_pricing`; `precio_aplicado` en línea = unitario lista ($300); subtotal de promo ≠ precio×cantidad cuando aplica 7/$2000 |
| Calculadora | Misma pad: en Pan pequeño interpreta **valor** (ceil); otras categorías = unidades / búsqueda por precio |
| Chips | `QToolButton` + clases `category-chip` / `product-chip` (no `payment-method-button`) |
| Imágenes | Sin archivo → sin icono / solo texto; no falla la UI |
| Formularios | Misma clase QSS en Crear y Editar (`product-form-field`) |
| stage0 timeout API | La prueba fuerza `API_PORT=1` para no flaquear si hay proceso en `:8765` |

## Cobertura §§20–23

| Sección | Archivos principales |
|---|---|
| §20 Pan pequeño | `tests/test_beta201_pan_pequeno_pricing.py`, `test_beta201_sales_pricing.py`, `test_beta201_desktop_sales.py` |
| §21 Otras categorías | `test_beta201_sales_pricing.py`, `test_beta201_desktop_sales.py` |
| §22 Interfaz | `test_beta201_catalog_chips.py`, `test_beta201_product_forms.py` |
| §23 Imágenes | `test_beta201_product_images.py` |
| Smoke | `test_beta2_smoke.py`, `test_beta201_smoke.py` |

## Sin regresiones de Beta 2.0

Se conservan CRUD productos, soft-delete, `POST /ventas` con líneas, snapshot histórico y legado value-only.
