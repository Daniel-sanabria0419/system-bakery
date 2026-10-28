# Database

## Base de datos

La aplicación utiliza:

SQLite

La base de datos es local y debe funcionar sin Internet.

## Esquema vigente (Beta 2.0 … Beta 2.0.4 Etapa 1)

Las tablas de catálogo y líneas (`categorias`, `productos`, `venta_lineas`) se introdujeron en **Beta 2.0 Etapa 1**.

- **Ventas nuevas (Beta 2):** siempre persisten `ventas.valor_total` **y** una o más filas en `venta_lineas` (snapshot de nombre/precio).
- **Legado Beta 1.x:** filas de `ventas` solo con `valor_total` **permanecen** sin `venta_lineas`. No se inventan líneas sintéticas.
- Durante el cobro, la lista de compra sigue viviendo solo en memoria hasta confirmar.
- **Beta 2.0.1 Etapa 1:** categoría «Pan pequeño» garantizada por nombre; columna nullable `productos.ruta_imagen`; carpetas `imagenes/categorias` y `imagenes/productos`.
- **Beta 2.0.4 Etapa 1:** tabla `promociones`; columna nullable `productos.promocion_id` (FK). Sin columnas promo en `venta_lineas` en esta etapa.
- **Beta 2.0.4 Etapa 2:** seed de promo canónica Pan pequeño + backfill de `promocion_id` en productos de esa categoría.
- **Beta 2.0.4 cutover + cierre:** cobro por FK/grupo; `venta_lineas.id_promocion` / `nombre_promocion` (snapshot, schema v3).
- **Meta:** tabla `schema_version` para migraciones ordenadas (ver sección Versión de esquema).

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

## Tabla: categorias (Beta 2.0 / 2.0.1)

Campos:

| Campo | Descripción |
|---|---|
| id_categoria | Identificador único de la categoría |
| nombre | Nombre de la categoría |

Semilla inicial si la tabla está vacía: Panadería, Pastelería, Bebidas, Snacks, Otros.

Además, al inicializar se ejecuta un **ensure por nombre** de la categoría **Pan pequeño** (`NOMBRE_CATEGORIA_PAN_PEQUENO`). Si ya existe (mismo nombre exacto), no se duplica. Si la base ya tenía las cinco categorías de Beta 2.0, se **añade** Pan pequeño sin borrar las anteriores.

La lógica especial de Pan pequeño (versiones posteriores de 2.0.1) debe resolver la categoría por **nombre**, no por `id_categoria` fijo.

No hay CRUD de categorías en Beta 2.0 / 2.0.1; solo listado y asociación desde productos / ventas. La lógica de precios de Pan pequeño (Beta 2.0.1) resuelve la categoría por **nombre**.

## Tabla: promociones (Beta 2.0.4 Etapa 1)

Campos:

| Campo | Descripción |
|---|---|
| id | Identificador único de la promoción |
| nombre | Nombre legible (p. ej. `Pan pequeño 7 por 2000`) |
| tipo | Tipo lógico en texto; primer valor previsto: `cantidad_por_monto` |
| configuracion | JSON en `TEXT` (no JSONB en SQLite); validado en aplicación |
| activo | 0/1 (soft off) |

Etapa 2 siembra una fila canónica (`Pan pequeño 7 por 2000`, tipo `cantidad_por_monto`, config JSON exacto `{"precio_base":300,"modo":"ceil"}`, `activo=1`). Packs 7/2000 y `todo_o_nada` son defaults del motor en código. **Etapa 5 cutover:** el cobro lee esta tabla vía `productos.promocion_id` (agrupación de carrito); ya no usa el nombre de categoría para montos. Schema v4 backfill reescribe configs antiguas al JSON slim.

**Invariante de ingresos / reportes:** `ventas.valor_total` = `SUM(venta_lineas.subtotal)`. No usar `SUM(precio_aplicado × cantidad)` (inflaría combos).

## Tabla: productos (Beta 2.0 / 2.0.1 / 2.0.4)

Campos:

| Campo | Descripción |
|---|---|
| id_producto | Identificador único del producto |
| nombre | Nombre del producto |
| precio | Precio actual en enteros (debe ser > 0) |
| id_categoria | Categoría del producto |
| descripcion | Descripción opcional (puede ser NULL) |
| id_estado | Estado activo / inactivo (mismo criterio que medios: activo = 1) |
| ruta_imagen | Ruta relativa opcional al archivo de imagen (nullable; p. ej. `imagenes/productos/...`) |
| promocion_id | FK nullable a `promociones(id)`. `NULL` = sin promo de tabla. Etapa 2: backfill a productos de «Pan pequeño»; expuesto en API; cobro aún no lo usa |

Un producto desactivado se conserva (soft-delete). No se elimina físicamente un producto referenciado en `venta_lineas`.

Las imágenes de producto viven bajo `imagenes/productos/` (ruta relativa en `ruta_imagen`, p. ej. `imagenes/productos/{id}.png`). Las de categoría (convención por archivo `imagenes/categorias/{id}.{ext}`, sin columna obligatoria) bajo `imagenes/categorias/`. Si el archivo falta, la UI no debe fallar.

## Tabla: venta_lineas (Beta 2.0 / 2.0.4)

Campos:

| Campo | Descripción |
|---|---|
| id_linea | Identificador único de la línea |
| id_venta | Venta a la que pertenece la línea |
| id_producto | Referencia al producto del catálogo |
| nombre_producto | Snapshot del nombre al momento de la venta |
| precio_aplicado | Snapshot del precio aplicado (entero > 0) |
| cantidad | Cantidad vendida (entero > 0) |
| subtotal | Subtotal de la línea (entero > 0). Puede ser ≠ `precio_aplicado × cantidad` con promo de grupo (`todo_o_nada` / combo). |
| id_promocion | Snapshot nullable de la promo aplicada (Beta 2.0.4) |
| nombre_promocion | Snapshot texto del nombre de promo (Beta 2.0.4); estable si la promo se renombra o desactiva después |

Las ventas antiguas (solo `valor_total`, sin detalle de productos) **permanecen sin filas** en `venta_lineas`. No se inventan líneas sintéticas.

**Invariante de totales:** el ingreso de una venta es `ventas.valor_total` (= `SUM(venta_lineas.subtotal)` en ventas nuevas). No usar `SUM(precio_aplicado × cantidad)` como métrica de ingresos (inflaría Pan pequeño en promo).

## Valores de caja y tendero

Para todas las ventas:

caja = 1

tendero = 1

## Relaciones

- `ventas.id_medio_pago` → `medios_pago.id_medio_pago`
- `productos.id_categoria` → `categorias.id_categoria`
- `productos.promocion_id` → `promociones.id` (nullable)
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
- tener estado activo o inactivo;
- poder tener `ruta_imagen` NULL;
- poder tener `promocion_id` NULL (o FK válida a `promociones`).

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

## Versión de esquema (`schema_version`)

Tabla meta:

| Campo | Descripción |
|---|---|
| version | Entero ≥ 0; una sola fila con la versión aplicada |

`CURRENT_SCHEMA_VERSION` en código es la versión objetivo. Las migraciones viven en `bakery/persistence/migrations.py` como lista ordenada `(versión, función)` y se aplican en orden desde la versión actual hasta la objetivo. Cada paso es **idempotente** respecto al estado físico (p. ej. `ALTER` solo si falta la columna).

Versión vigente:

| Versión | Contenido |
|---|---|
| 0 | Sin meta (bases antiguas o vacías antes de este mecanismo) |
| 1 | Baseline Beta 2.0.1: tablas de catálogo/líneas, `productos.ruta_imagen` si faltaba |
| 2 | Beta 2.0.4 Etapa 1: tabla `promociones`; `productos.promocion_id` nullable FK |
| 3 | Beta 2.0.4 cierre: `venta_lineas.id_promocion` + `nombre_promocion` |

## Migración

Al llamar `initialize`, se ejecuta:

1. `CREATE TABLE IF NOT EXISTS` para todas las tablas de negocio (incl. `promociones` y `schema_version`);
2. migraciones ordenadas hasta `CURRENT_SCHEMA_VERSION` (hoy: v3 = snapshot promo en `venta_lineas`);
3. semilla de medios (si la tabla está vacía);
4. semilla de categorías Beta 2.0 (si la tabla está vacía);
5. ensure de «Pan pequeño» por nombre;
6. ensure de promo canónica Pan pequeño + backfill de `promocion_id` en productos de esa categoría (Beta 2.0.4 Etapa 2);
7. creación idempotente de `imagenes/categorias` y `imagenes/productos` en la raíz del proyecto.

Es idempotente:

- en una base nueva: esquema completo, `schema_version = CURRENT`, semillas, Pan pequeño y promo canónica;
- en una base con las cinco categorías de Beta 2.0: se añade Pan pequeño, `ruta_imagen` y `promocion_id`, promo + backfill, y se marca `schema_version`;
- en una base en v1: se crea `promociones` y se añade `promocion_id` sin tocar datos de venta; luego seed/backfill;
- en una base solo-`medios_pago` / `ventas`: agrega tablas faltantes sin alterar ventas existentes;
- re-ejecutar `initialize` no duplica datos ni re-aplica migraciones ya aplicadas.
