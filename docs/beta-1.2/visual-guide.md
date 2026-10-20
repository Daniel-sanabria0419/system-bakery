# Guía de personalización visual — Beta 1.2

Esta guía indica **dónde** cambiar la apariencia del desktop con **Beta 1.2 terminada**, más el **pulido visual post-1.2** aplicado en el checkout local (métricas y colores leídos del working tree; el código de esos tweaks puede aún no estar en `main`).

Parte de la guía de Beta 1.1 y documenta los seis ajustes UX/estéticos de 1.2 (medio de pago, diálogos, volver, layout, menú) y el pulido posterior.

- **Colores y tipografía:** archivo QSS [`bakery/desktop/theme.qss`](../../bakery/desktop/theme.qss).
- **Márgenes / espaciados / tamaños mínimos de layout:** [`bakery/desktop/style.py`](../../bakery/desktop/style.py).

**Precedencia:** para el botón volver, el tamaño y color visibles se definen en `theme.qss` (`min-width` / `min-height` / `padding` / colores). Las constantes `BACK_BUTTON_MIN_*` en `style.py` alimentan `setMinimumSize` en `ui.py`; el look acordado se edita en QSS.

## Clases QSS

En Qt las clases se asignan con la propiedad dinámica `class` (`style.apply_class(widget, "...")`).

| Clase | Widgets | Qué editar en `theme.qss` |
|---|---|---|
| `pad-button` | Dígitos, `00`, Borrar, C, Agregar, Pago | `QPushButton[class="pad-button"]` |
| `money-text` | `sale_display`, `purchase_list`, `purchase_total` | `QLabel[class="money-text"]` (entrada grande: `#sale_display`) |
| `back-button` | Flecha atrás (sin texto «Volver»); fondo `#5ac4f6`, texto blanco | `QPushButton[class="back-button"]` |
| `menu-button` | Registrar venta (menú; fondo `#2E7D32`) | `QPushButton[class="menu-button"]` |
| `payment-button` | Botón de medio de pago en registrar venta | `QPushButton[class="payment-button"]` |
| `payment-method-button` | Botones del popup de medios | `QPushButton[class="payment-method-button"]` |
| `dialog-text` | Etiquetas de confirmar / venta guardada | `QLabel[class="dialog-text"]` |
| `dialog-action-button` | Confirmar, No, Aceptar | `QPushButton[class="dialog-action-button"]` (min-height ~80 px) |

También en `theme.qss` (por selector / `#objectName`):

- Fondo de ventana y diálogos: `QMainWindow, QDialog` → `#F5F0E8`
- Panel de compra: `#purchase_panel` → `#FFFFFF`
- Lista y scroll: `#purchase_list`, `#purchase_list_scroll` (y viewport) → fondo `#FFFFFF`; texto de lista `#1A1A1A`
- Separadores: `#entry_separator`, `#total_separator`

El QSS se carga en la `QApplication` desde [`bakery/desktop/main.py`](../../bakery/desktop/main.py) (`load_theme_qss()`).

Ya no se usa `QComboBox` / clase `combo-box` para medios de pago.

## Layout metrics (`style.py`)

| Constante | Controla |
|---|---|
| `PAGE_MARGIN` | Márgenes de las pantallas (registrar venta) |
| `MENU_MARGIN` | Márgenes del menú (~20 px) |
| `MENU_BUTTON_COLOR` | Color acordado del botón menú (`#2E7D32`) |
| `PAGE_SPACING` | Espacio vertical / entre columnas |
| `LEFT_COLUMN_STRETCH` / `RIGHT_COLUMN_STRETCH` | Proporción columnas |
| `PURCHASE_PANEL_STRETCH` / `PAD_PANEL_STRETCH` | Detalle ~1/3 vs pad ~2/3 en registrar venta |
| `PAD_SPACING` | Espacio entre teclas del pad |
| `PAD_BUTTON_MIN_WIDTH` / `PAD_BUTTON_MIN_HEIGHT` | Tamaño mínimo de teclas (0 = sin forzar) |
| `PAYMENT_METHOD_BUTTON_MIN_WIDTH` / `PAYMENT_METHOD_BUTTON_MIN_HEIGHT` | Tamaño mínimo de botones del popup de medios |
| `DIALOG_ACTION_BUTTON_MIN_HEIGHT` / `DIALOG_ACTION_BUTTON_MIN_WIDTH` | Botones Confirmar / No / Aceptar (~80 px de alto) |
| `DIALOG_MIN_WIDTH` / `DIALOG_MIN_HEIGHT` | Área mínima de diálogos confirmar / éxito |
| `DIALOG_CONTENT_MARGIN` / `DIALOG_CONTENT_SPACING` | Márgenes y espaciado internos de esos diálogos |
| `BACK_BUTTON_MIN_WIDTH` / `BACK_BUTTON_MIN_HEIGHT` | `setMinimumSize` del volver (`72` × `29`); el tamaño pintado se ajusta sobre todo en QSS |

Helpers:

- `load_theme_qss()` — lee `theme.qss`
- `apply_class(widget, name)` — asigna la clase QSS

## Modo de ventana

Pantalla completa en [`bakery/desktop/ui.py`](../../bakery/desktop/ui.py) (`MainWindow` → `showFullScreen()`).

## Layout Registrar venta

```text
[ ← ] …stretch…   (flecha atrás a la izquierda; objectName back_button)
[ purchase_panel ~1/3 ]  [ future_panel vacío ]
[ pad_panel ~2/3      ]
```

### Botón volver (Etapa 2 + pulido post-1.2)

- Visible: ícono Unicode `←` (no el texto «Volver»); color de flecha blanco (`color: #FFFFFF` en QSS).
- Posición: a la **izquierda** de la barra superior (`addWidget(back)` y luego `addStretch(1)`).
- Fondo: `#5ac4f6` (clase `back-button`).
- Tamaño efectivo (QSS, look acordado):
  - `min-width: 72px`
  - `min-height: 20px`
  - `padding: 4px 8px`
  - `font-size: 30px`
- Constantes en `style.py` (para `setMinimumSize`): `BACK_BUTTON_MIN_WIDTH = 72`, `BACK_BUTTON_MIN_HEIGHT = 29`.
- Forma: más ancho que alto. El pulido local lo dejó **más compacto** que el 96×72 de cierre de la etapa 2.
- Tooltip «Volver»; misma acción: regresar al menú conservando estado.

### Layout detalle / pad (Etapa 3 + pulido)

- Proporción vertical en la columna izquierda: `purchase_panel` stretch 1, `pad_panel` stretch 2 (~1/3 y ~2/3).
- Líneas agregadas dentro de `purchase_list_scroll` (`QScrollArea`):
  - Barras de scroll **ocultas**: `ScrollBarAlwaysOff` en vertical y horizontal (sigue habiendo scroll por rueda / gesto).
  - Fondo blanco: `#purchase_list_scroll`, su viewport y `#purchase_list` → `#FFFFFF`; texto de lista `#1A1A1A`.
- Tipografía de líneas: `#purchase_list` a 28 px; `#sale_display` y `#purchase_total` permanecen en 36 px.

Pad:

| | Col0 | Col1 | Col2 | Col3 |
|---|---|---|---|---|
| R0 | 1 | 2 | 3 | Borrar |
| R1 | 4 | 5 | 6 | C |
| R2 | 7 | 8 | 9 | Pago (2 filas) |
| R3 | 0 | 00 | Agregar | (Pago) |

- Todas las teclas del pad usan `QSizePolicy.Preferred` × `QSizePolicy.Expanding` (crecen en altura con el panel).
- QSS `pad-button`: `margin: 10px 3px`; `font-size: 28px`; `font-weight: bold`; fondo `#D0D0D0`.

Texto del botón de cobro: **Pago** (`objectName` = `submit_sale_button`, clase `pad-button`).

### Medio de pago (Etapa 0)

- Botón en el pie del panel de compra: `payment_button`.
  - Sin selección: «Seleccionar medio de pago».
  - Con selección: «Medio de pago: {nombre}».
- Al pulsarlo se abre `SelectPaymentMethodDialog` (`select_payment_dialog`).
- Dentro del diálogo: un botón grande por medio activo (`payment_method_{id_medio_pago}`), en filas de máximo 5.
- El diálogo solo se cierra al tocar un medio (Escape / rechazo del sistema no cierran; sin botón de cerrar en la barra).
- Se puede reabrir para cambiar el medio.

### Menú principal (Etapa 4)

- Botón «Registrar venta» arriba a la izquierda con margen `MENU_MARGIN` (~20 px).
- Fondo `#2E7D32` (clase `menu-button`).
- Contenedor `menu_grid` (`QGridLayout`) con stretch en fila/columna 1: preparado para una grilla futura; no se añaden más botones en esta etapa.

### Diálogos confirmar / éxito (Etapa 1 + pulido)

- `ConfirmSaleDialog` (`confirm_dialog`) y `SaleSavedDialog` (`sale_saved_dialog`) son más grandes que en 1.1.
- Texto: clase `dialog-text` (fuente ~28 px en QSS).
- Botones de acción: clase `dialog-action-button`, altura mínima ~80 px (`style.DIALOG_ACTION_BUTTON_MIN_HEIGHT` y `min-height: 80px` en QSS).
- Centrado horizontal de la fila de botones: `QDialogButtonBox.setCenterButtons(True)` en ambos diálogos.
- objectNames estables: `confirm_value_label`, `confirm_payment_label`, `confirm_button`, `cancel_button`, `sale_saved_message`, `sale_saved_ok_button`.

## Widgets y objectName

Archivo principal: [`bakery/desktop/ui.py`](../../bakery/desktop/ui.py)

| objectName | Widget | Clase QSS |
|---|---|---|
| `menu_grid` | Contenedor grilla del menú (listo para más botones) | — |
| `menu_register_button` | Registrar venta (arriba-izquierda, `#2E7D32`) | `menu-button` |
| `back_button` | Flecha atrás `←` (izquierda; `#5ac4f6`) | `back-button` |
| `left_column` | Columna operativa | — |
| `purchase_panel` | Panel blanco | `#purchase_panel` en QSS |
| `sale_display` | Entrada actual | `money-text` |
| `entry_separator` | Separador bajo la entrada | `#entry_separator` |
| `purchase_list_scroll` | Scroll de líneas (barras AlwaysOff; fondo blanco) | `#purchase_list_scroll` |
| `purchase_list` | Líneas agregadas (fuente 28 px; fondo blanco) | `money-text` + `#purchase_list` |
| `pad_panel` | Contenedor del teclado (~2/3) | — |
| `total_separator` | Separador sobre total/medio | `#total_separator` |
| `purchase_total` | Total acumulado | `money-text` |
| `payment_button` | Medio de pago (abre popup) | `payment-button` |
| `select_payment_dialog` | Popup de medios | — |
| `payment_method_{id}` | Opción de medio en el popup | `payment-method-button` |
| `digit_0` … `digit_9`, `digit_00` | Teclas | `pad-button` |
| `borrar_button`, `clear_button`, `agregar_button` | Teclas | `pad-button` |
| `submit_sale_button` | Pago | `pad-button` |
| `future_panel` | Espacio derecho vacío | — |
| `confirm_dialog` | Popup confirmar venta | — |
| `confirm_value_label`, `confirm_payment_label` | Texto del confirmar | `dialog-text` |
| `confirm_button`, `cancel_button` | Confirmar / No (centrados) | `dialog-action-button` |
| `sale_saved_dialog` | Popup venta guardada | — |
| `sale_saved_message` | Mensaje de éxito | `dialog-text` |
| `sale_saved_ok_button` | Aceptar (centrado) | `dialog-action-button` |

## Cómo cambiar cada aspecto

| Qué | Dónde |
|---|---|
| Colores / tipografía / fondos | `theme.qss` |
| Márgenes / espaciado / min size pad / botones de medios | `style.py` |
| Tamaño / color del volver | Preferir `theme.qss` (`back-button`); `BACK_BUTTON_MIN_*` solo para `setMinimumSize` |
| Pantalla completa / ventana | `MainWindow` en `ui.py` |
| Posición de teclas | Lista `pad_buttons` en `ui.py` |

Ejemplo en `theme.qss` (valores vigentes del fondo común):

```css
QMainWindow,
QDialog {
    background-color: #F5F0E8;
}

QPushButton[class="pad-button"] {
    background-color: #D0D0D0;
    color: rgb(0, 0, 0);
    margin: 10px 3px;
    font-size: 28px;
    font-weight: bold;
}
```

## Qué no hace Beta 1.2

- No define una paleta de marca definitiva más allá de los seis ajustes acordados y el pulido post-1.2 documentado aquí.
- No introduce un framework de temas múltiples (dark/light).
- No llena el `future_panel` con funcionalidades nuevas.
- No añade productos, sync, login ni lógica de negocio nueva.
- Cambiar solo `theme.qss` / métricas de `style.py` no altera la lógica de negocio.
