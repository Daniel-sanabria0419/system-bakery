# Etapas de implementación — Beta 1.2

Documento de referencia para implementar Beta 1.2 por etapas.

Beta 1.2 es una versión de ajustes estéticos y UX táctil sobre Beta 1.1.
Preserva contratos de API y SQLite. No añade lógica de negocio nueva.

No implementar funcionalidades fuera del alcance de Beta 1.2.

## Decisiones acordadas

| # | Decisión | Detalle |
|---|---|---|
| 1 | Medio de pago | Quitar el select (`payment_combo` / `QComboBox`). Botón con texto inicial «Seleccionar medio de pago». Al elegir un medio, el botón muestra «Medio de pago: {nombre}». Popup con botones grandes; una fila de máximo 5; si hay más medios, otra fila. El popup solo se cierra al tocar un medio. Se puede volver a abrir para cambiar la selección. |
| 2 | Popups confirmar / éxito | `ConfirmSaleDialog` y `SaleSavedDialog`: todo más grande (texto y diálogo). Botones de acción ~80 px de alto. |
| 3 | Botón volver | Ícono de flecha atrás; sin texto «Volver». Forma: rectángulo un poco más ancho que alto; un poco más grande que el actual. |
| 4 | Layout registrar venta | Panel de detalle/compra ~1/3 de la altura útil; pad de calculadora ~2/3. Si hay muchas líneas, scroll en el detalle. Solo aumentar el tamaño de fuente de las **líneas agregadas** (`purchase_list`); no subir el de total ni el de la entrada en curso (`sale_display`, `purchase_total`). |
| 5 | Menú | Botón «Registrar venta» arriba a la izquierda, margen ~20 px (preparado para una grilla futura de botones). Color de fondo `#2E7D32`. |
| 6 | Alcance | Solo cambios estéticos / UX táctil listados arriba. Sin productos, sync, login ni lógica de negocio nueva. Preservar contratos API/SQLite. |

Comportamientos de Beta 1.1 que **no** cambian:

- Entrada / compra / total; AGREGAR, Borrar, C; formato COP.
- Pago habilitado solo si total > 0 y hay medio seleccionado.
- Confirmación previa al POST; popup de éxito solo tras POST exitoso.
- Volver al menú conserva compra, entrada y medio seleccionado.
- Tras éxito: limpiar entrada, compra y medio; permanecer en registrar venta.
- HTTP solo al cargar medios y al confirmar venta.

## Estado de etapas

| Etapa | Nombre | Estado |
|---|---|---|
| 0 | Medio de pago: botón + popup (+ docs iniciales 1.2) | Hecha |
| 1 | Popups confirmar y éxito más grandes | Hecha |
| 2 | Botón volver con ícono | Hecha |
| 3 | Layout registrar venta (proporciones, scroll, fuente) | Hecha |
| 4 | Menú: posición y color | Hecha |
| 5 | Regresión completa (+ doc final) | Pendiente |

## Etapa 0 — Medio de pago: botón + popup

**Hecha.** Reemplazó el `QComboBox` (`payment_combo`) por:

- Botón `payment_button` (clase `payment-button`): texto «Seleccionar medio de pago» / «Medio de pago: {nombre}».
- Diálogo `SelectPaymentMethodDialog` (`select_payment_dialog`) con botones `payment_method_{id}` (clase `payment-method-button`), máx. 5 por fila.
- Cierre solo al elegir un medio (`reject` / Escape no cierran; sin botón de cerrar en la barra).
- Misma semántica que 1.1 para Pago, volver y reset post-éxito.
- Sin cambios en API, SQLite ni capa `app`.

## Etapa 1 — Popups confirmar y éxito más grandes

**Hecha.** Agrandó `ConfirmSaleDialog` y `SaleSavedDialog` para uso táctil:

- Texto de diálogo con clase `dialog-text` (fuente mayor en QSS).
- Botones de acción (`confirm_button`, `cancel_button`, `sale_saved_ok_button`) con clase `dialog-action-button` y altura mínima ~80 px (`DIALOG_ACTION_BUTTON_MIN_HEIGHT`).
- Área mínima del diálogo vía `DIALOG_MIN_WIDTH` / `DIALOG_MIN_HEIGHT` y márgenes de contenido.
- Flujo funcional idéntico (Confirmar/No; Aceptar tras éxito; mismo momento del POST).

## Etapa 2 — Botón volver con ícono

**Hecha.** Reemplazó el texto «Volver» por un ícono de flecha atrás (`←`):

- `objectName` estable: `back_button`; clase `back-button`.
- Forma rectangular un poco más ancha que alta (`BACK_BUTTON_MIN_WIDTH` > `BACK_BUTTON_MIN_HEIGHT`); un poco más grande que el control de texto anterior.
- Misma navegación: vuelve al menú sin limpiar compra, entrada ni medio.
- Tooltip «Volver» para accesibilidad; la etiqueta visible no es «Volver».

## Etapa 3 — Layout registrar venta (proporciones, scroll, fuente)

**Hecha.** Repartió la columna operativa ~1/3 detalle / ~2/3 pad:

- Stretch `PURCHASE_PANEL_STRETCH = 1` y `PAD_PANEL_STRETCH = 2` (`pad_panel`).
- Lista de líneas en `QScrollArea` (`purchase_list_scroll`) para muchas líneas.
- Fuente mayor solo en `QLabel#purchase_list` (28 px); `sale_display` y `purchase_total` siguen en 36 px.

## Etapa 4 — Menú: posición y color

**Hecha.** Reubicó «Registrar venta» arriba a la izquierda:

- Margen `MENU_MARGIN = 20` px; contenedor `menu_grid` (`QGridLayout`) con stretch en fila/columna 1 para una grilla futura (sin botones extra).
- Color de fondo `#2E7D32` (`menu-button` en QSS / `MENU_BUTTON_COLOR`).
- Sigue siendo el único botón del menú; misma navegación a registrar venta.

El detalle de objetivos, archivos y criterios está en el plan de Beta 1.2 del Project.
