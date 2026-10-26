# Database

## Base de datos

La aplicación utiliza:

SQLite

La base de datos es local y debe funcionar sin Internet.

## Esquema vigente (Beta 2.0)

Las tablas de catálogo y líneas (`categorias`, `productos`, `venta_lineas`) se introdujeron en **Beta 2.0 Etapa 1**.

- **Ventas nuevas (Beta 2):** siempre persisten `ventas.valor_total` **y** una o más filas en `venta_lineas` (snapshot de nombre/precio).
- **Legado Beta 1.x:** filas de `ventas` solo con `valor_total` **permanecen** sin `venta_lineas`. No se inventan líneas sintéticas.
- Durante el cobro, la lista de compra sigue viviendo solo en memoria hasta confirmar.

Beta 1.1 y 1.2 no cambiaron el esquema; este documento describe el esquema **actual** tras Beta 2.

## Tabla: medios_pago

Campos:

| Campo | Descripción |
|---|---|
| id_medio_pago | Identificador único del medio de pago |
| nombre | Nombre del medio de pago |
| id_estado | Estado del medio de pago |

Los medios de pago con estado activo estarán disponibles para seleccionar en la interfaz.

## Tabla: ventas

Campos:

| Campo | Descripción |
|---|---|
| id_venta | UUID en texto, generado al registrar la venta |
| valor_total | Valor total de la venta |
| fecha_venta | Fecha y hora del registro |
| id_medio_pago | Medio de pago utilizado |
| caja | Identificador de caja |
| tendero | Identificador del tendero |

## Tabla: categorias (Beta 2.0)

Campos:

| Campo | Descripción |
|---|---|
| id_categoria | Identificador único de la categoría |
| nombre | Nombre de la categoría |

Semilla inicial (idempotente si la tabla está vacía): Panadería, Pastelería, Bebidas, Snacks, Otros.

No hay CRUD de categorías en Beta 2.0; solo listado y asociación desde productos / ventas.

## Tabla: productos (Beta 2.0)

Campos:

| Campo | Descripción |
|---|---|
| id_producto | Identificador único del producto |
| nombre | Nombre del producto |
| precio | Precio actual en enteros (debe ser > 0) |
| id_categoria | Categoría del producto |
| descripcion | Descripción opcional (puede ser NULL) |
| id_estado | Estado activo / inactivo (mismo criterio que medios: activo = 1) |

Un producto desactivado se conserva (soft-delete). No se elimina físicamente un producto referenciado en `venta_lineas`.

## Tabla: venta_lineas (Beta 2.0)

Campos:

| Campo | Descripción |
|---|---|
| id_linea | Identificador único de la línea |
| id_venta | Venta a la que pertenece la línea |
| id_producto | Referencia al producto del catálogo |
| nombre_producto | Snapshot del nombre al momento de la venta |
| precio_aplicado | Snapshot del precio aplicado (entero > 0) |
| cantidad | Cantidad vendida (entero > 0) |
| subtotal | Subtotal de la línea (entero > 0; precio × cantidad) |

Las ventas antiguas (solo `valor_total`, sin detalle de productos) **permanecen sin filas** en `venta_lineas`. No se inventan líneas sintéticas.

## Valores de caja y tendero

Para todas las ventas:

caja = 1

tendero = 1

## Relaciones

- `ventas.id_medio_pago` → `medios_pago.id_medio_pago`
- `productos.id_categoria` → `categorias.id_categoria`
- `venta_lineas.id_venta` → `ventas.id_venta`
- `venta_lineas.id_producto` → `productos.id_producto`

## Valor monetario

`valor_total`, `precio`, `precio_aplicado` y `subtotal` se almacenan como número entero.

No almacenar:

"$ 25.000"

Debe almacenarse:

25000

El formato monetario se aplica únicamente en la interfaz.

## Reglas

Una venta debe:

- tener un ID UUID almacenado como TEXT;
- tener un valor mayor que 0;
- tener un medio de pago válido;
- tener fecha y hora;
- tener caja = 1;
- tener tendero = 1.

Una venta **nueva** (Beta 2) debe además tener ≥ 1 fila en `venta_lineas` cuya suma de subtotales coincida con `valor_total`.

Un producto debe:

- tener precio entero mayor que 0;
- tener una categoría válida;
- tener estado activo o inactivo.

Una línea de venta (cuando exista) debe:

- referenciar una venta y un producto válidos;
- guardar snapshot de nombre y precio aplicado;
- tener cantidad > 0 y subtotal > 0.

## Integridad

La base de datos debe impedir, cuando sea apropiado:

- ventas sin valor;
- valores menores o iguales a 0;
- referencias inexistentes a medios de pago;
- productos con precio ≤ 0;
- referencias inexistentes a categorías;
- líneas con cantidad ≤ 0, subtotal ≤ 0 o precio_aplicado ≤ 0;
- referencias inexistentes a ventas o productos en `venta_lineas`.

## Migración

Al llamar `initialize`, se ejecuta `CREATE TABLE IF NOT EXISTS` para todas las tablas (incluidas las nuevas). Es idempotente:

- en una base nueva: crea el esquema completo y siembra medios y categorías;
- en una base que solo tenía `medios_pago` / `ventas`: agrega las tablas faltantes sin alterar filas existentes de ventas.
