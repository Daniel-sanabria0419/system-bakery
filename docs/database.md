# Database

## Base de datos

La aplicación utiliza:

SQLite

La base de datos es local y debe funcionar sin Internet.

## Beta 1.1 y Beta 1.2 — esquema

**Beta 1.1 y Beta 1.2 no requieren cambios de esquema.**

La lista temporal de valores de la compra vive solo en memoria (capa de aplicación / desktop) durante el registro de la venta.

Al confirmar, se persiste únicamente el total acumulado como `ventas.valor_total`, igual que en Beta 1.

No se agregan:

- tablas de líneas de detalle de venta;
- columnas para ítems de compra temporales;
- tablas de productos.

El resto de este documento describe el esquema vigente (establecido en Beta 1).

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

## Valores de caja y tendero

Para todas las ventas (Beta 1 y Beta 1.1):

caja = 1

tendero = 1

## Relaciones

ventas.id_medio_pago referencia:

medios_pago.id_medio_pago

## Valor monetario

valor_total debe almacenarse como número entero.

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

## Integridad

La base de datos debe impedir, cuando sea apropiado:

- ventas sin valor;
- valores menores o iguales a 0;
- referencias inexistentes a medios de pago.