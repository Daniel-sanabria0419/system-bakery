# Architecture

## Objetivo

La arquitectura debe permitir construir una aplicación de escritorio sencilla y evolucionarla sin reescribir el proyecto.

Beta 1 estableció las capas. Beta 1.1 las reutiliza: solo cambia el flujo de registro en desktop y la lógica local de entrada/compra.

Beta 1.2 reutiliza las mismas capas y contratos; solo ajusta UX/estética en desktop (sin cambios de API, `app` ni SQLite).

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
| Desktop | `bakery/desktop` | Pantallas, navegación, diálogos; sin reglas de negocio |
| Cliente HTTP | `bakery/desktop/client.py` | `GET /medios-pago`, `POST /ventas`; `GET /health` solo comprueba la API |
| API | `bakery/api` | Rutas delgadas; validación HTTP |
| Aplicación | `bakery/app` | Entrada/calculadora, compra en memoria, registro de venta, formato COP |
| Persistencia | `bakery/persistence` | Schema SQLite, repositorios |

## Flujo desktop (Beta 1.1 / 1.2)

```text
Menú principal
      |
      | Registrar venta
      v
Registrar venta
  - entrada actual (calculadora local)
  - lista de compra (memoria)
  - total acumulado
  - medio de pago (botón → popup de medios; sin QComboBox)
  - Volver (ícono ←) → menú (conserva estado)
      |
      | Pago (habilitado si total > 0 y hay medio)
      v
Diálogo confirmar (antes del POST)
      |
      | Confirmar
      v
POST /ventas  { valor_total = total compra, id_medio_pago }
      |
      +-- error → mensaje de error; no popup de éxito; no limpiar como éxito
      |
      +-- ok → popup "Venta guardada"
                → limpiar entrada + compra (+ selección de medio)
                → permanecer en Registrar venta
```

### Selección de medio de pago (Beta 1.2)

- Desktop: botón `payment_button` abre `SelectPaymentMethodDialog`.
- Los medios siguen viniendo de `GET /medios-pago` vía `ApiClient.list_payment_methods()`.
- Sin endpoint nuevo; la capa `app` y la persistencia no participan en la UI de selección.

## Separación de estado (Beta 1.1)

En la capa `app` (sin Qt) deben distinguirse:

1. **Entrada actual** — dígitos que el usuario está escribiendo en la calculadora.
2. **Compra** — lista en memoria de valores enteros ya agregados.
3. **Total** — suma de la compra; es el `valor_total` que se envía a la API.

La lista de compra **no** se persiste en SQLite como líneas. Solo se guarda el total al confirmar la venta.

### Contrato de display de la entrada

La presentación monetaria de la entrada actual vive en la capa `app` (`Calculator.display_text()`), reutilizando `format_cop`:

- Sin dígitos → cadena vacía `""` (no `$ 0`).
- Con dígitos → `format_cop(current_amount)` (ej. `1000` → `$ 1.000`).
- Incluye el caso `0` mientras el usuario tiene un cero en la entrada → `$ 0`.
- Es lógica local: no hay HTTP al formatear ni al pulsar dígitos.

La UI desktop debe consumir este texto; no debe recalcular el formato por su cuenta salvo presentación de ítems/total de compra (también vía `format_cop`).

### Responsabilidades de controles

| Control | Responsabilidad |
|---|---|
| Dígitos | Actualizan solo la entrada actual (local, sin HTTP) |
| **AGREGAR** | Si la entrada es un entero > 0, la añade a la compra, actualiza el total y limpia solo la entrada |
| **Borrar** | Elimina un dígito de la entrada actual; no modifica la compra |
| **C** | Limpia la compra completa y deja la entrada lista para empezar de nuevo; no cambia el medio de pago |
| Medio de pago | Abre el popup de medios; al elegir, actualiza el botón; no hace HTTP salvo la carga inicial de medios |
| **Pago** | Usa el total de la compra + medio de pago; abre confirmación; luego POST |
| Volver (`←`, sin texto «Volver») | Cambia a la pantalla de menú **sin** limpiar entrada ni compra |

Los botones `+` y `−` de Beta 1 dejan de existir; no hay evaluación de expresiones con operadores.

## Comunicación con la API

La calculadora y la compra son locales.

La API nombra dos rutas de negocio:

- cargar medios de pago (`GET /medios-pago`);
- registrar la venta confirmada (`POST /ventas` con el total acumulado).

Hay una ruta adicional, `GET /health`, solo para comprobar que la API está en funcionamiento. Se usa en el arranque.

No debe existir un endpoint de calculadora ni peticiones por cada tecla.

## Navegación entre pantallas

- `QStackedWidget` (u equivalente) mantiene las páginas en memoria.
- Al volver al menú no se destruye la pantalla de registro; el estado pendiente se conserva.
- Tras una venta guardada con éxito sí se limpia el estado de registro.

## Popup posterior al guardado

- Responsabilidad de la capa desktop.
- Solo tras respuesta exitosa del `POST /ventas`.
- Distinto del diálogo de confirmación *previa* al POST.
- El diálogo de confirmación decide si se intenta guardar; el popup de éxito informa que el guardado ocurrió.
- En Beta 1.2 (etapa 1), ambos diálogos son más grandes para uso táctil: texto con clase `dialog-text`, botones de acción ~80 px (`dialog-action-button`). Sin cambio de cuándo se hace el POST.

## Personalización visual

La apariencia se controla en la capa desktop:

- Constantes de tamaño/márgenes/espaciado: [`bakery/desktop/style.py`](../bakery/desktop/style.py)
- Widgets y `objectName`: [`bakery/desktop/ui.py`](../bakery/desktop/ui.py)
- Guía práctica vigente: [`docs/beta-1.2/visual-guide.md`](beta-1.2/visual-guide.md) (histórico 1.1: [`docs/beta-1.1/visual-guide.md`](beta-1.1/visual-guide.md))

No hay un framework de temas obligatorio ni paleta de marca fijada. Los widgets usan `objectName` para poder aplicar `setStyleSheet` después, sin cambiar la arquitectura.

## Principios que se mantienen

- La interfaz no contiene lógica de negocio.
- El acceso a datos está separado de la lógica de negocio.
- La aplicación funciona sin Internet.
- El dinero no usa floats.
- Las ventas tienen identificadores únicos (UUID).
- No introducir abstracciones innecesarias ni funcionalidades fuera de alcance.

## Fuera de alcance arquitectónico (Beta 1.1 / 1.2)

- Nuevas tablas para líneas de venta.
- Nuevos endpoints innecesarios.
- Mover la calculadora al backend.
- Cambiar SQLite o introducir PostgreSQL.
- Productos, inventario, sync o login.
