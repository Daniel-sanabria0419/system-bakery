# Guía de personalización visual — Beta 1.2

Esta guía indica **dónde** cambiar la apariencia en el estado actual del desktop (Beta 1.2 en curso).

Parte de la guía de Beta 1.1 y sustituye el select de medio de pago por botón + popup.

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
| `payment-button` | Botón de medio de pago en registrar venta | `QPushButton[class="payment-button"]` |
| `payment-method-button` | Botones del popup de medios | `QPushButton[class="payment-method-button"]` |

También en `theme.qss` (por `#objectName`):

- Fondo de ventana: `QMainWindow`
- Panel de compra: `#purchase_panel`
- Separadores: `#entry_separator`, `#total_separator`

El QSS se carga en la `QApplication` desde [`bakery/desktop/main.py`](../../bakery/desktop/main.py) (`load_theme_qss()`).

Ya no se usa `QComboBox` / clase `combo-box` para medios de pago.

## Layout metrics (`style.py`)

| Constante | Controla |
|---|---|
| `PAGE_MARGIN` | Márgenes de las pantallas |
| `PAGE_SPACING` | Espacio vertical / entre columnas |
| `LEFT_COLUMN_STRETCH` / `RIGHT_COLUMN_STRETCH` | Proporción columnas |
| `PAD_SPACING` | Espacio entre teclas del pad |
| `PAD_BUTTON_MIN_WIDTH` / `PAD_BUTTON_MIN_HEIGHT` | Tamaño mínimo de teclas (0 = sin forzar) |
| `PAYMENT_METHOD_BUTTON_MIN_WIDTH` / `PAYMENT_METHOD_BUTTON_MIN_HEIGHT` | Tamaño mínimo de botones del popup de medios |

Helpers:

- `load_theme_qss()` — lee `theme.qss`
- `apply_class(widget, name)` — asigna la clase QSS

## Modo de ventana

Pantalla completa en [`bakery/desktop/ui.py`](../../bakery/desktop/ui.py) (`MainWindow` → `showFullScreen()`).

## Layout Registrar venta

```text
[ Volver ]
[ panel compra + pad ]  [ future_panel vacío ]
```

Pad:

| | Col0 | Col1 | Col2 | Col3 |
|---|---|---|---|---|
| R0 | 1 | 2 | 3 | Borrar |
| R1 | 4 | 5 | 6 | C |
| R2 | 7 | 8 | 9 | Pago (2 filas) |
| R3 | 0 | 00 | Agregar | (Pago) |

Texto del botón de cobro: **Pago** (`objectName` = `submit_sale_button`, clase `pad-button`).

### Medio de pago (Etapa 0)

- Botón en el pie del panel de compra: `payment_button`.
  - Sin selección: «Seleccionar medio de pago».
  - Con selección: «Medio de pago: {nombre}».
- Al pulsarlo se abre `SelectPaymentMethodDialog` (`select_payment_dialog`).
- Dentro del diálogo: un botón grande por medio activo (`payment_method_{id_medio_pago}`), en filas de máximo 5.
- El diálogo solo se cierra al tocar un medio (Escape / rechazo del sistema no cierran; sin botón de cerrar en la barra).
- Se puede reabrir para cambiar el medio.

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
| `payment_button` | Medio de pago (abre popup) | `payment-button` |
| `select_payment_dialog` | Popup de medios | — |
| `payment_method_{id}` | Opción de medio en el popup | `payment-method-button` |
| `digit_0` … `digit_9`, `digit_00` | Teclas | `pad-button` |
| `borrar_button`, `clear_button`, `agregar_button` | Teclas | `pad-button` |
| `submit_sale_button` | Pago | `pad-button` |
| `future_panel` | Espacio derecho vacío | — |
| `confirm_*` / `sale_saved_*` | Diálogos | (sin clase por ahora) |

## Cómo cambiar cada aspecto

| Qué | Dónde |
|---|---|
| Colores / tipografía / fondos | `theme.qss` |
| Márgenes / espaciado / min size pad / botones de medios | `style.py` |
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

## Qué no hace Beta 1.2 (todavía / nunca en esta versión)

- Etapas 1–5 pendientes: popups más grandes, ícono volver, proporciones 1/3–2/3, menú verde, regresión.
- No define una paleta de marca definitiva más allá de los ajustes acordados.
- No introduce un framework de temas múltiples (dark/light).
- No llena el `future_panel` con funcionalidades nuevas.
- Cambiar solo `theme.qss` / métricas de `style.py` no altera la lógica de negocio.
