# Guía de personalización visual — Beta 1.1

Documento histórico de Beta 1.1. Para el estado actual del desktop (Beta 1.2), ver [`docs/beta-1.2/visual-guide.md`](../beta-1.2/visual-guide.md). En 1.2 el medio de pago ya no usa `payment_combo` / `QComboBox`.

Esta guía indica **dónde** cambiar la apariencia en el estado de Beta 1.1.

- **Colores y tipografía:** archivo QSS [`bakery/desktop/theme.qss`](../../bakery/desktop/theme.qss).
- **Márgenes / espaciados / tamaños mínimos de layout:** [`bakery/desktop/style.py`](../../bakery/desktop/style.py).

## Clases QSS

En Qt las clases se asignan con la propiedad dinámica `class` (`style.apply_class(widget, "...")`).

| Clase | Widgets | Qué editar en `theme.qss` |
|---|---|---|
| `pad-button` | Dígitos, `00`, Borrar, C, Agregar, Pago | `QPushButton[class="pad-button"]` |
| `money-text` | `sale_display`, `purchase_list`, `purchase_total` | `QLabel[class="money-text"]` (entrada grande: `#sale_display`) |
| `back-button` | Volver | `QPushButton[class="back-button"]` |
| `menu-button` | Registrar venta (menú) | `QPushButton[class="menu-button"]` |

También en `theme.qss` (por `#objectName`):

- Fondo de ventana: `QMainWindow`
- Panel de compra: `#purchase_panel`
- Separadores: `#entry_separator`, `#total_separator`

El QSS se carga en la `QApplication` desde [`bakery/desktop/main.py`](../../bakery/desktop/main.py) (`load_theme_qss()`).

## Layout metrics (`style.py`)

| Constante | Controla |
|---|---|
| `PAGE_MARGIN` | Márgenes de las pantallas |
| `PAGE_SPACING` | Espacio vertical / entre columnas |
| `LEFT_COLUMN_STRETCH` / `RIGHT_COLUMN_STRETCH` | Proporción columnas |
| `PAD_SPACING` | Espacio entre teclas del pad |
| `PAD_BUTTON_MIN_WIDTH` / `PAD_BUTTON_MIN_HEIGHT` | Tamaño mínimo de teclas (0 = sin forzar) |

Helpers:

- `load_theme_qss()` — lee `theme.qss`
- `apply_class(widget, name)` — asigna la clase QSS

## Modo de ventana

Pantalla completa en [`bakery/desktop/ui.py`](../../bakery/desktop/ui.py) (`MainWindow` → `showFullScreen()`).

## Layout Registrar venta

```text
[ Volver ]
[ panel compra + pad ]  [ future_panel  ← vacío en 1.1; catálogo desde Beta 2+ ]
```

> Guía **histórica** de Beta 1.1. `#future_panel` hoy es el panel de catálogo (nombre legado).

Pad:

| | Col0 | Col1 | Col2 | Col3 |
|---|---|---|---|---|
| R0 | 1 | 2 | 3 | Borrar |
| R1 | 4 | 5 | 6 | C |
| R2 | 7 | 8 | 9 | Pago (2 filas) |
| R3 | 0 | 00 | Agregar | (Pago) |

Texto del botón de cobro: **Pago** (`objectName` = `submit_sale_button`, clase `pad-button`).

## Widgets y objectName

Archivo principal: [`bakery/desktop/ui.py`](../../bakery/desktop/ui.py)

| objectName | Widget | Clase QSS |
|---|---|---|
| `menu_register_button` | Botón menú | `menu-button` |
| `back_button` | Volver | `back-button` |
| `left_column` | Columna operativa | — |
| `purchase_panel` | Panel blanco | `#purchase_panel` en QSS |
| `sale_display` | Entrada actual | `money-text` |
| `entry_separator` | Separador bajo la entrada | `#entry_separator` |
| `purchase_list` | Líneas agregadas | `money-text` |
| `total_separator` | Separador sobre total/medio | `#total_separator` |
| `purchase_total` | Total acumulado | `money-text` |
| `payment_combo` | Medio de pago | — |
| `digit_0` … `digit_9`, `digit_00` | Teclas | `pad-button` |
| `borrar_button`, `clear_button`, `agregar_button` | Teclas | `pad-button` |
| `submit_sale_button` | Pago | `pad-button` |
| `future_panel` | Espacio derecho (vacío en 1.1; catálogo desde Beta 2+) | — |
| `confirm_*` / `sale_saved_*` | Diálogos | (sin clase por ahora) |

## Cómo cambiar cada aspecto

| Qué | Dónde |
|---|---|
| Colores / tipografía / fondos | `theme.qss` |
| Márgenes / espaciado / min size pad | `style.py` |
| Pantalla completa / ventana | `MainWindow` en `ui.py` |
| Posición de teclas | Lista `pad_buttons` en `ui.py` |

Ejemplo en `theme.qss`:

```css
QMainWindow {
    background-color: #2B2B2B;
}

QPushButton[class="pad-button"] {
    background-color: #E8E8E8;
    color: #111111;
}
```

## Qué no hace Beta 1.1

- No define una paleta de marca definitiva (solo valores iniciales editables en QSS).
- No introduce un framework de temas múltiples (dark/light).
- No llenaba el `future_panel` con funcionalidades nuevas (catálogo llegó en Beta 2+).
- Cambiar solo `theme.qss` / métricas de `style.py` no altera la lógica de negocio.
