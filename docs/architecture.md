# Architecture

## Objetivo

La arquitectura debe permitir construir una aplicación de escritorio sencilla y evolucionarla sin reescribir el proyecto.

Beta 1 estableció las capas. Beta 1.1 las reutiliza cambiando el flujo de registro. Beta 1.2 solo ajusta UX/estética en desktop.

**Beta 2.0** reutiliza las mismas capas y añade catálogo de productos, líneas de venta y un contrato nuevo de `POST /ventas`, preservando offline, dinero en enteros y la UX táctil de 1.2.

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
| Desktop | `bakery/desktop` | Pantallas (menú, productos, registrar venta), navegación, diálogos; sin reglas de negocio |
| Cliente HTTP | `bakery/desktop/client.py` | Medios, productos/categorías, `POST /ventas` con líneas; `GET /health` al arranque |
| API | `bakery/api` | Rutas delgadas; validación HTTP |
| Aplicación | `bakery/app` | Calculadora, compra con líneas (`PurchaseLine` / `SaleDraft`), productos, `register_sale`, formato COP |
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
4. Calculadora = búsqueda por precio + rechazo duro sin producto.
5. UI Productos separada de UI de cobro.
6. Solo soft-delete de productos.
7. Ventas antiguas value-only sin backfill de líneas.

Detalle: `docs/beta-2/stages.md` y resumen de cierre en el Context del proyecto.

## Fuera de alcance arquitectónico (Beta 2.0)

- Historial avanzado / edición de ventas.
- Inventario, recetas, producción, clientes, sync, login, reportes.
- ORM / framework de migraciones pesado.
- Mover la calculadora al backend.
- PostgreSQL funcional.
