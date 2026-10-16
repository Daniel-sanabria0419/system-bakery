# Guía de personalización visual — Beta 1.1

Esta guía indica **dónde** cambiar la apariencia. No impone colores, tipografías ni un diseño concreto.

## Constantes centralizadas

Archivo: [`bakery/desktop/style.py`](../../bakery/desktop/style.py)

| Constante | Controla |
|---|---|
| `WINDOW_WIDTH` / `WINDOW_HEIGHT` | Tamaño inicial de la ventana |
| `PAGE_MARGIN_*` | Márgenes de las pantallas |
| `PAGE_SPACING` | Espacio vertical entre bloques |
| `PAD_SPACING` | Espacio entre teclas del pad |
| `PAD_BUTTON_MIN_WIDTH` / `PAD_BUTTON_MIN_HEIGHT` | Tamaño mínimo de teclas (0 = sin forzar) |

Ejemplo: para botones del pad más grandes, pon `PAD_BUTTON_MIN_WIDTH = 64` y `PAD_BUTTON_MIN_HEIGHT = 48`.

## Widgets y objectName

Archivo principal: [`bakery/desktop/ui.py`](../../bakery/desktop/ui.py)

| objectName | Widget | Uso típico |
|---|---|---|
| `menu_register_button` | Botón menú | Texto, tamaño, color |
| `back_button` | Volver | Posición/estilo |
| `sale_display` | Entrada con formato | Tipografía grande, alineación |
| `purchase_title` | Título "Compra" | Tipografía |
| `purchase_list` | Líneas agregadas | Tipografía, altura |
| `purchase_total` | Total acumulado | Tipografía, énfasis |
| `digit_0` … `digit_9` | Teclas numéricas | Tamaño/color |
| `borrar_button` | Borrar | Estilo |
| `clear_button` | C | Estilo |
| `agregar_button` | AGREGAR | Estilo destacado |
| `payment_combo` | Medio de pago | Ancho |
| `submit_sale_button` | Registrar venta | Estilo CTA |
| `confirm_dialog` | Diálogo previo al POST | Contenedor |
| `confirm_value_label` / `confirm_payment_label` | Textos del diálogo | Tipografía |
| `confirm_button` / `cancel_button` | Botones confirmar/no | Estilo |
| `sale_saved_dialog` | Popup post-éxito | Contenedor |
| `sale_saved_message` | Mensaje de éxito | Tipografía |
| `sale_saved_ok_button` | Aceptar del popup | Estilo |

## Cómo cambiar cada aspecto

| Qué | Dónde | Cómo |
|---|---|---|
| Tamaño ventana | `style.py` → `WINDOW_*` | Enteros en píxeles |
| Márgenes / espaciado | `style.py` → `PAGE_*`, `PAD_SPACING` | Enteros |
| Tamaño botones del pad | `style.py` → `PAD_BUTTON_MIN_*` | Enteros (> 0 aplica `setMinimumSize`) |
| Posición de teclas | `RegisterSalePage` en `ui.py` | Tuplas `(texto, fila, columna)` del pad |
| Orden de bloques | `RegisterSalePage.__init__` | Orden de `layout.addWidget(...)` |
| Textos de botones | Literales en `ui.py` | p. ej. `"AGREGAR"`, `"Volver"` |
| Colores / tipografía | Cualquier widget con `objectName` | `widget.setStyleSheet(...)` o QSS por `#objectName` |

Ejemplo de estilo por objectName (opcional, tú decides los valores):

```python
self._display.setStyleSheet("#sale_display { font-size: 28px; }")
```

o a nivel de ventana:

```python
self.setStyleSheet("#agregar_button { font-weight: bold; }")
```

## Qué no hace Beta 1.1

- No define una paleta de marca.
- No introduce un framework de temas.
- No cambia el comportamiento funcional al editar solo `style.py`.
