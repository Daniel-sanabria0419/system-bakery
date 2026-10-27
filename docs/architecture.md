# Architecture

## Objetivo

La arquitectura debe permitir construir una aplicación de escritorio sencilla y evolucionarla sin reescribir el proyecto.

Beta 1 estableció las capas. Beta 1.1 las reutiliza cambiando el flujo de registro. Beta 1.2 solo ajusta UX/estética en desktop.

**Beta 2.0** reutiliza las mismas capas y añade catálogo de productos, líneas de venta y un contrato nuevo de `POST /ventas`, preservando offline, dinero en enteros y la UX táctil de 1.2.

**Beta 2.0.1** añade precios especiales de Pan pequeño (módulo en `app`), modo valor en cobro para esa categoría, chips de catálogo, imágenes de producto y estilo unificado de formularios — sin cambiar el contrato de `POST /ventas` ni inventar un motor genérico de promociones.

**Beta 2.0.2** evoluciona solo UX de cobro/catálogo: prefijo de precio en grilla (capa `app` + desktop), wrap/`#d7d4ce`/panel seleccionado y listado Productos blanco — sin cambiar `POST /ventas` ni el módulo de promo.

**Beta 2.0.3** añade navegación de catálogo en dos vistas (categorías ↔ productos + Volver) y métricas/tipografía de chips editables en `style.py` — sin cambiar API ni promo.

## Arquitectura general

```text
PySide6 / Qt
      |
      v
Aplicación local (desktop)
      |
      v
FastAPI
      |
      v
Lógica de aplicación (app)
      |
      v
Persistencia
      |
      v
SQLite
```

## Capas y responsabilidades

| Capa | Paquete | Responsabilidad |
|---|---|---|
| Desktop | `bakery/desktop` | Pantallas (menú, productos, registrar venta), navegación, diálogos; sin reglas de negocio. Módulos: `main_window`, `menu_page`, `register_sale_page`, `products_page`, `dialogs`, `ui_helpers`; `ui.py` reexporta la API pública |
| Cliente HTTP | `bakery/desktop/client.py` | Medios, productos/categorías, `POST /ventas` con líneas; `GET /health` al arranque |
| API | `bakery/api` | Rutas delgadas; validación HTTP |
| Aplicación | `bakery/app` | Calculadora, compra con líneas (`PurchaseLine` / `SaleDraft`), productos, `pan_pequeno_pricing`, imágenes de producto, `register_sale`, formato COP |
| Persistencia | `bakery/persistence` | Schema SQLite, repositorios (medios, productos, ventas + líneas) |

## Flujo desktop (Beta 2.0)

```text
Menú principal
  - Registrar venta
  - Productos
      |
      +-- Productos → listar / crear / editar / activar-desactivar
      |
      +-- Registrar venta
            - panel catálogo (categorías + productos activos + cantidad)
            - entrada (calculadora = búsqueda por precio exacto)
            - lista de compra (nombre × cantidad — subtotal)
            - total acumulado
            - medio de pago (botón → popup; sin QComboBox)
            - Volver (←) → menú (conserva estado)
            |
            | Pago (total > 0 y medio)
            v
          Diálogo confirmar
            |
            | Confirmar
            v
          POST /ventas  { id_medio_pago, lineas: [...] }
            |
            +-- error → mensaje; no éxito; no limpiar como éxito
            |
            +-- ok → popup "Venta guardada"
                      → limpiar entrada + compra + medio
                      → permanecer en Registrar venta
```

### Selección de medio de pago (Beta 1.2, vigente)

- Desktop: botón `payment_button` abre `SelectPaymentMethodDialog`.
- Medios desde `GET /medios-pago` vía `ApiClient.list_payment_methods()`.

## Separación de estado (Beta 2.0)

En la capa `app` (sin Qt):

1. **Entrada actual** — dígitos de la calculadora (local, sin HTTP por tecla).
2. **Producto seleccionado** — requerido para agregar una línea.
3. **Compra** — lista en memoria de `PurchaseLine` (producto, nombre, precio aplicado, cantidad, subtotal).
4. **Total** — suma de subtotales; el backend recalcula/valida al registrar.

La lista de compra **no** se persiste hasta confirmar. Al confirmar se guardan `ventas` + `venta_lineas` (snapshot).

### Contrato de display de la entrada

La presentación monetaria de la entrada actual vive en `Calculator.display_text()` / `format_cop`.

Comportamiento vigente en código (conservado a propósito en Beta 2):

- Sin dígitos / vacío → `"$ 0.00"` (desajuste histórico respecto a docs 1.1 que pedían `""`; no se corrigió en Beta 2 sin OK explícito).
- Con dígitos → `format_cop(current_amount)` (ej. `1000` → `$ 1.000`).

La UI desktop consume este texto; no recalcula el formato por su cuenta salvo ítems/total vía `format_cop`.

### Responsabilidades de controles (venta)

| Control | Responsabilidad |
|---|---|
| Dígitos | Actualizan la entrada; alimentan búsqueda local por precio exacto (candidatos activos) |
| Catálogo / categoría | Selección de producto activo; cantidad |
| **AGREGAR** | Si hay producto seleccionado → añade línea y limpia entrada; si no → rechazo visible |
| **Borrar** | Elimina un dígito de la entrada; no modifica la compra |
| **C** | Limpia compra y entrada; no cambia el medio de pago |
| Medio de pago | Popup de medios (carga inicial vía API) |
| **Pago** | Confirmación → POST con líneas |
| Volver (`←`) | Menú **sin** limpiar entrada ni compra |

## Comunicación con la API

Rutas de negocio vigentes:

| Método | Ruta | Uso |
|---|---|---|
| GET | `/health` | Arranque |
| GET | `/medios-pago` | Medios activos |
| GET | `/categorias` | Listado de categorías |
| GET | `/productos` | Listado (incl. inactivos; admin UI) |
| GET | `/productos/activos` | Activos; query opcional `id_categoria`, `precio` |
| GET | `/productos/{id}` | Detalle |
| POST | `/productos` | Crear |
| PUT | `/productos/{id}` | Editar |
| POST | `/productos/{id}/activar` | Activar |
| POST | `/productos/{id}/desactivar` | Desactivar |
| POST | `/ventas` | Registrar venta con líneas |

`POST /ventas` body:

```text
{ "id_medio_pago": int, "lineas": [ { "id_producto", "cantidad", "precio_aplicado" }, ... ] }
```

No hay endpoint de calculadora ni HTTP por tecla. La búsqueda por precio en UI usa catálogo ya cargado / `list_active_products` según el flujo; los dígitos son locales.

## Navegación entre pantallas

- `QStackedWidget` mantiene las páginas en memoria.
- Al volver al menú no se destruye el registro; el estado pendiente se conserva.
- Tras venta exitosa se limpia el estado de registro.
- Productos es una sección aparte; no se mezcla CRUD de catálogo dentro del popup de cobro.

## Popup posterior al guardado

- Responsabilidad desktop.
- Solo tras `POST /ventas` exitoso.
- Distinto del diálogo de confirmación previa.
- Diálogos táctiles 1.2: texto `dialog-text`, botones ~80 px (`dialog-action-button`).

## Personalización visual

- Colores/tipografía: [`bakery/desktop/theme.qss`](../bakery/desktop/theme.qss)
- Constantes: [`bakery/desktop/style.py`](../bakery/desktop/style.py)
- Widgets: [`bakery/desktop/ui.py`](../bakery/desktop/ui.py)
- Guía: [`docs/beta-1.2/visual-guide.md`](beta-1.2/visual-guide.md)

## Principios que se mantienen

- La interfaz no contiene lógica de negocio.
- El acceso a datos está separado de la lógica de negocio.
- La aplicación funciona sin Internet.
- El dinero no usa floats.
- Las ventas tienen identificadores únicos (UUID).
- No introducir abstracciones innecesarias ni funcionalidades fuera de alcance.

## Decisiones arquitectónicas Beta 2.0 (resumen)

1. Categorías como entidad mínima con semilla; sin CRUD UI.
2. Snapshot en `venta_lineas` para integridad histórica.
3. `POST /ventas` con líneas; total en backend; sin dual-shape legacy.
4. Calculadora = búsqueda por precio + rechazo duro sin producto *(Beta 2.0.2: prefijo en grilla en lugar de UI de búsqueda exacta)*.
5. UI Productos separada de UI de cobro.
6. Solo soft-delete de productos.
7. Ventas antiguas value-only sin backfill de líneas.

Detalle: `docs/beta-2/stages.md` y resumen de cierre en el Context del proyecto.

## Beta 2.0.1 (resumen)

- Detección Pan pequeño por **nombre** de categoría.
- Precios solo en `bakery/app/pan_pequeno_pricing.py` (sin floats); promo 7/$2000 solo si cantidad % 7 == 0 (sin “grupos + resto”).
- Calculadora: valor + ceil para Pan pequeño; resto como Beta 2.0.
- Persistencia: `schema_version` + migraciones ordenadas en `bakery/persistence/migrations.py` (sin ORM).
- `ruta_imagen` nullable; archivos bajo `imagenes/productos/`; categorías por convención de archivo.
- Chips y formularios: clases QSS dedicadas (`category-chip` / `product-chip` / `product-form-field`).

Detalle: `docs/beta-2.0.1/stages.md`.

## Beta 2.0.2 (resumen)

- `candidates_by_price_prefix` en `purchase.py`; UI sin `price_search_*`.
- Tres modos de pad: prefijo / valor Pan pequeño / cantidad.
- `FlowLayout` + secciones `#d7d4ce` + divisor negro; panel seleccionado con imagen/unitario/subtotal.
- Listado Productos: fondo `#FFFFFF` (QSS); no alterar `payment-method-button`.

Detalle: `docs/beta-2.0.2/stages.md`.

## Beta 2.0.3 (resumen)

- Vista A (solo categorías) / Vista B (productos + chip Volver); `catalog_back_to_categories`.
- Chips: `CATEGORY_CHIP_*` / `PRODUCT_CHIP_*` / `*_FONT_SIZE` en `style.py`; QSS vía `load_theme_qss`.
- `CatalogChipButton` para nombres multilínea.

Detalle: `docs/beta-2.0.3/stages.md`.

## Fuera de alcance arquitectónico (Beta 2.0 / 2.0.1 / 2.0.2 / 2.0.3)

- Historial avanzado / edición de ventas.
- Inventario, recetas, producción, clientes, sync, login, reportes.
- Motor genérico/configurable de promociones.
- ORM / framework de migraciones pesado.
- Mover la calculadora al backend.
- PostgreSQL funcional.
