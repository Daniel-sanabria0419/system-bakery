# Database — Beta 1

## Base de datos

Beta 1 utiliza:

SQLite

La base de datos es local y debe funcionar sin Internet.

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

## Valores de Beta 1

Para todas las ventas:

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