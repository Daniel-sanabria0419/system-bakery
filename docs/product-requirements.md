# Product Requirements

## Objetivo general

Crear una aplicación de escritorio para registrar ventas de una panadería.

## Versiones

| Versión | Estado | Objetivo |
|---|---|---|
| Beta 1 | Completada (referencia) | Registrar una venta y almacenarla localmente |
| Beta 1.1 | Completada | Mejorar el flujo de registro con lista de compra en memoria y UX de calculadora |
| Beta 1.2 | Completada | Ajustes estéticos / UX táctil; sin lógica de negocio nueva |
| Beta 2.0 | Implementada (código); cierre documental Etapa 10 | Productos (CRUD), categorías, venta con líneas y filtro por precio |
| Beta 2.0.1 | **Terminada** 2026-10-26 (OK final Daniel) | Pan pequeño (promo), cobro por valor, chips, imágenes, formularios |
| Beta 2.0.2 | **Terminada** 2026-10-27 (OK final Daniel) | Layout cobro, prefijo de precio, listado Productos blanco |
| Beta 2.0.3 | **Terminada** 2026-10-27 (OK final Daniel) | Navegación catálogo Vista A/B; chips más grandes / tipografía editable |
| Beta 2.0.4 | **Terminada** 2026-10-27 (OK final Daniel) | Migrar Pan pequeño a `promociones` + FK; cobro por FK/grupo |
| Beta 2.0.5 | **En curso** | Cobro `cantidad_por_monto`: menor múltiplo de 1000 con `ceil(monto/precio_base) >= qty` |

---

# Beta 2.0.5 (en curso)

## Objetivo

Cobrar `cantidad_por_monto` con la inversa de la tabla valor→cantidad: tras agrupar por `promocion_id`, el monto es el menor múltiplo de 1000 tal que `ceil(monto / precio_base) >= cantidad` del grupo.

Detalle: `docs/beta-2.0.5/stages.md`. Diseño: Context `docs/beta-2.0.5-promo-por-producto-y-grupo.md`.

## Comportamiento

- Cobro: menor múltiplo de 1000 con `ceil(monto / precio_base) >= cantidad` del grupo (4→1000, 7→2000, 10→3000, 14→4000, 17→5000, 20→6000, 24→7000, 27→8000, 30→9000, 34→10000).
- Carrito: suma qty del mismo `promocion_id` y después esa fórmula (4+3→2000; 7+5→4000).
- JSON slim `precio_base`+`modo`; ceil valor→qty sin cambio.

## Fuera del alcance de Beta 2.0.5

CRUD rico de promos, otros tipos, inventario, sync, login, reportes, PostgreSQL, Beta 2.1+.

---

# Beta 2.0.4 (terminada)

## Objetivo

Reemplazar la promo hardcodeada de Pan pequeño (`pan_pequeno_pricing` por nombre de categoría) por filas en `promociones` + `productos.promocion_id`, con cálculo tipado `cantidad_por_monto` y **agrupación en todo el carrito** (`todo_o_nada`).

Detalle: `docs/beta-2.0.4/stages.md`. Plan: Context `docs/beta-2.0.4-promociones-plan.md`. Cierre: Context `docs/beta-2.0.4-closure.md`.

## Etapas 1–7 (hechas #39–#44)

- Schema, seed, dual-path, UI carrito, cutover (flag default True).
- Snapshot `venta_lineas` (`id_promocion` / `nombre_promocion`); regresión + docs (`docs/beta-2.0.4/regression-notes.md`).
- Cobro por FK/grupo `cantidad_por_monto` (`todo_o_nada`); sin montos por nombre de categoría.

## Fuera del alcance de Beta 2.0.4

CRUD rico de promos en UI, otros tipos de promo, inventario, sync, login, reportes, PostgreSQL, reabrir UX 2.0.3.

---

# Beta 2.0.3 (terminada)

## Objetivo

Mejorar el cobro: al elegir categoría o Todos, pasar a una vista solo de productos con chip Volver; chips más grandes y tipografía editable en `style.py` — sin lógica de negocio nueva ni features 2.1+.

Detalle: `docs/beta-2.0.3/stages.md`. Regresión: `docs/beta-2.0.3/regression-notes.md`.

## Cobro / catálogo

- Vista A: solo categorías; ningún chip empieza seleccionado (Todos tampoco).
- Categoría o Todos → Vista B: productos + chip Volver en la grilla; categorías ocultas.
- Volver restaura Vista A (listo para elegir otra vez).
- Prefijo / Pan pequeño / panel seleccionado: sin cambio respecto a 2.0.2.
- Tamaños y `font-size` de chips: constantes en `bakery/desktop/style.py` (vigente: categoría/producto **135×120**, fuente 16 px).

## Fuera del alcance de Beta 2.0.3

Historial, órdenes, clientes, recetas, inventario, promos genéricas, Beta 2.1+.

---

# Beta 2.0.2 (terminada)

## Objetivo

Pulir el cobro: filtro por **prefijo** de precio en la grilla (sin UI de búsqueda exacta), layout wrap de categorías/productos, panel de selección mejorado y listado Productos con fondo blanco — sin motor de promos nuevo ni features 2.1+.

Detalle: `docs/beta-2.0.2/stages.md`. Regresión: `docs/beta-2.0.2/regression-notes.md`.

## Cobro / catálogo

- Sin producto seleccionado: dígitos filtran productos por prefijo de `precio` (string del entero), acotado a la categoría activa (Todos = todas).
- Con producto: Pan pequeño = valor→cantidad; resto = cantidad/`+/-`; sin filtro prefijo.
- Sin bloque «Búsqueda por precio».
- Categorías/productos en filas wrap según ancho (~6 de referencia, no fijo).
- Fondos de sección `#d7d4ce`; divisor negro entre categorías y productos.
- Panel seleccionado: imagen, nombre, unitario + subtotal; a la derecha cantidad luego −/+.

## Pantalla Productos

- Fondo del listado **blanco** (`#FFFFFF`).

## Fuera del alcance de Beta 2.0.2

Historial, órdenes, clientes, recetas, inventario, promos genéricas, Beta 2.1+.

---

# Beta 2.0.1 (terminada)

## Objetivo

Añadir la categoría **Pan pequeño** con promoción fija (7 panes / $2000), calculadora por valor en cobro para esa categoría, y mejoras de UI de catálogo, imágenes y formularios Crear/Editar — sin motor genérico de promociones ni features de 2.1+.

Detalle de etapas: `docs/beta-2.0.1/stages.md`. Regresión: `docs/beta-2.0.1/regression-notes.md`.

## Pan pequeño

- Categoría garantizada por **nombre** (no por id fijo).
- Precio unitario de lista: **$300**.
- Promo fija **solo si la cantidad es múltiplo exacto de 7**: cada bloque de exactamente 7 panes cuesta **$2000** (ahorro vs 7×$300). **No** se combina “grupos + resto”: 6 panes = $1800; 7 = $2000; 8 = $2400 (sin promo parcial); 14 = $4000.
- La promo refleja “cada $2000 de pan” como combo cerrado de 7; cantidades que no cierran el combo se cobran a unitario.
- Cantidades siempre enteras; valores inválidos redondean **hacia arriba** (ceil); el usuario ve el resultado antes de Agregar.
- `+/-` recalcula cantidad y subtotal (promo solo si queda múltiplo de 7).
- Otras categorías: por unidades; sin promo Pan pequeño.
- En `venta_lineas`, `precio_aplicado` = unitario de lista ($300); el `subtotal` puede ser distinto de `precio_aplicado × cantidad` cuando aplica la promo.

## UI catálogo / imágenes / formularios

- Botón **Todos** primero; chips color `#64c466`. Métricas al cierre de 2.0.1: 93×70 / 87×60; **vigentes** (Beta 2.0.3): `CATEGORY_CHIP_*` / `PRODUCT_CHIP_*` en `style.py` (**135×120**).
- Estructura `imagenes/categorias` y `imagenes/productos`; asociar imagen al crear/editar producto; sin archivo no rompe la UI.
- Crear y Editar producto: mismo estilo; placeholders más oscuros que el fondo; texto negro; select alineado a inputs.

## Fuera del alcance de Beta 2.0.1

Igual que Beta 2.0, más: sistema configurable de promociones, flag `tiene_promocion` por producto, Beta 2.1+.

---

# Beta 2.0 (implementada)

## Objetivo

Evolucionar el registro de ventas de una lógica basada en montos sueltos a una lógica basada en **productos**, preservando lo de Beta 1.2 que no conflictúa (UX táctil, capas, offline, dinero en enteros).

Detalle de etapas: `docs/beta-2/stages.md`. Notas de regresión: `docs/beta-2/regression-notes.md`.

## Productos

Sección **Productos** desde el menú:

- Crear: nombre, precio (entero > 0), categoría, descripción opcional; estado activo.
- Editar: mismos campos permitidos.
- Activar / desactivar (soft-delete): desactivado no aparece en ventas nuevas ni en búsqueda por precio; se conserva; no hay DELETE físico de productos usados en líneas.

Cada producto tiene **un único precio actual**. Sin variantes ni listas de precios.

## Categorías

- Entidad independiente (`categorias`) con semilla inicial.
- Asociación obligatoria al crear/editar producto.
- Agrupación / filtro al seleccionar productos en una venta.
- **Sin CRUD de categorías en UI** en Beta 2.0.

## Registrar venta (vigente)

- Catálogo de productos **activos** (por categoría) en el panel de venta (`#future_panel`; nombre legado; es el panel de catálogo).
- Cantidad por línea; subtotal = precio × cantidad en el caso general; **excepción Beta 2.0.1:** Pan pequeño puede tener subtotal de promo (ver sección Pan pequeño). Total = suma de subtotales (siempre recalculado en backend).
- Calculadora: dígitos locales. **Vigente (2.0.2+):** sin producto seleccionado, filtran la grilla por **prefijo** de precio (`candidates_by_price_prefix`). En 2.0 la búsqueda era exacta; `candidates_by_exact_price` / `GET /productos/activos?precio=` / `find_active_products_by_price` quedan como **legado API/helper** (tests y contrato HTTP); el desktop de cobro **no** los usa.
- **AGREGAR** exige producto seleccionado; sin selección → rechazo con feedback visible (no se agrega monto suelto).
- Lista de compra muestra nombre, cantidad y subtotal.
- Medio de pago: mismo patrón 1.2 (botón + popup).
- Confirmación previa → `POST /ventas` → popup de éxito → limpiar y permanecer en registrar venta.

## Contrato de registro

```text
POST /ventas
{
  "id_medio_pago": int,
  "lineas": [
    { "id_producto": int, "cantidad": int, "precio_aplicado": int },
    ...
  ]
}
```

El backend valida productos activos, calcula subtotales y `valor_total`, y persiste `ventas` + `venta_lineas` (con snapshot de nombre y precio) en una transacción. El shape antiguo solo-`valor_total` se rechaza.

## Legado value-only

Las ventas de Beta 1.x guardadas solo con `valor_total` **permanecen** sin filas en `venta_lineas`. No se inventan productos ni líneas sintéticas. Las ventas nuevas siempre tienen ≥ 1 línea.

## Fuera del alcance de Beta 2.0

No implementar:

- historial avanzado de ventas;
- edición / eliminación / corrección de ventas;
- pedidos / clientes de pedidos;
- recetas / ingredientes / costos / márgenes;
- inventario / stock / producción;
- múltiples precios o variantes;
- CRUD UI de categorías;
- sync nube, PostgreSQL funcional, login, reportes, IA.

---

# Beta 1.2 (completada)

## Objetivo

Mejorar la usabilidad táctil y la apariencia del flujo de registro de ventas, sin cambiar qué se guarda ni cómo se calcula. Preserva API y SQLite de Beta 1.1.

## Decisiones (lista cerrada)

1. **Medio de pago:** botón «Seleccionar medio de pago» / «Medio de pago: {nombre}»; popup con botones grandes (máx. 5 por fila); cierra solo al elegir; se puede reabrir para cambiar. Sin `QComboBox`.
2. **Popups confirmar / éxito:** texto y diálogo más grandes; botones ~80 px de alto.
3. **Volver:** ícono de flecha atrás (sin texto); rectángulo un poco más ancho que alto.
4. **Layout registrar venta:** detalle ~1/3, pad ~2/3; scroll en el detalle; solo subir fuente de líneas agregadas.
5. **Menú:** «Registrar venta» arriba a la izquierda, margen ~20 px; color `#2E7D32`.
6. **Alcance:** solo esos cambios; sin productos, sync, login ni lógica de negocio nueva.

## Estado de implementación

| Etapa | Estado |
|---|---|
| 0 Medio de pago: botón + popup | Hecha |
| 1 Popups confirmar y éxito más grandes | Hecha |
| 2 Botón volver con ícono | Hecha |
| 3 Layout registrar venta | Hecha |
| 4 Menú: posición y color | Hecha |
| 5 Regresión completa (+ doc final) | Hecha |

**Beta 1.2 está cerrada** a nivel de alcance implementado (regresión en verde; 67 pruebas). Detalle: `docs/beta-1.2/stages.md`. Guía visual: `docs/beta-1.2/visual-guide.md`.

Pulido visual posterior (colores/métricas/layout táctil; sin cambio de lógica ni de las seis decisiones): documentado en la misma guía visual.

## Medio de pago (vigente tras Etapa 0)

En registrar venta:

- Un botón abre un popup con los medios activos (`GET /medios-pago`).
- Texto inicial del botón: «Seleccionar medio de pago».
- Tras elegir: «Medio de pago: {nombre}».
- El popup solo se cierra al tocar un medio; se puede reabrir para cambiar.
- **Pago** sigue habilitado solo si el total es mayor que 0 y hay medio seleccionado.
- Volver al menú conserva el medio; tras venta exitosa se limpia la selección.

No hay select / combo de medios de pago.

---

# Beta 1.1 (completada)

## Objetivo

Evolucionar el registro de venta para que funcione como una pequeña lista de compra acumulada, sin productos ni catálogo, preservando la arquitectura y la persistencia de Beta 1.

## Pantallas

### 1. Menú principal

Debe mostrar:

- Botón "Registrar venta".

En Beta 1.2: arriba a la izquierda, margen ~20 px, color de fondo `#2E7D32`; layout preparado para una grilla futura sin añadir más botones ahora.

No debe contener otras funcionalidades en Beta 1.1 / 1.2.

### 2. Registrar venta

Debe permitir:

- Introducir un valor monetario mediante una calculadora numérica local.
- Ver el valor de la entrada actual con formato monetario mientras se escribe.
- Agregar el valor actual a una lista de compra con el botón **AGREGAR**.
- Ver la lista de valores agregados y el total acumulado.
- Borrar un dígito a la vez de la entrada actual (**Borrar**).
- Limpiar completamente la compra y la entrada actual (**C**).
- Seleccionar un medio de pago (en Beta 1.2: botón + popup; ver sección Beta 1.2).
- Registrar la venta con el total acumulado mediante el botón **Pago**.
- Volver al menú anterior (ícono de flecha atrás; sin texto «Volver») conservando el estado de la compra pendiente.

No debe mostrar botones `+` ni `−`.

### 3. Confirmación previa al guardado

Al presionar **Pago**, debe aparecer una confirmación.

Debe mostrar:

- Valor total (total de la compra).
- Medio de pago seleccionado.

Debe contener:

- Botón "Confirmar".
- Botón "No".

La venta solamente se envía a la API después de presionar "Confirmar".

### 4. Confirmación de venta guardada

Después de un `POST /ventas` exitoso, debe mostrarse un popup indicando que la venta fue guardada correctamente.

Si el registro falla:

- no debe mostrarse el mensaje de éxito;
- debe mostrarse un comportamiento de error apropiado;
- el estado de la compra debe permanecer coherente (no limpiarse como si hubiera tenido éxito).

## Calculadora y compra

### Entrada actual (calculadora)

La calculadora es local (sin HTTP por tecla) y solo maneja la entrada en curso:

- Números enteros.
- Formato monetario en tiempo real (ej. `1000` → `$ 1.000`).
- **Borrar**: elimina un dígito de la entrada actual.
- No opera sobre los valores ya agregados a la compra.

### Lista de compra

Cada elemento de la compra es únicamente un valor monetario entero.

Ejemplo de flujo:

1. Usuario escribe `5000` → se muestra `$ 5.000`.
2. Pulsa **AGREGAR** → la compra muestra `$ 5.000`, total `$ 5.000`; la entrada queda lista para el siguiente valor.
3. Usuario escribe `3000` → se muestra `$ 3.000`.
4. Pulsa **AGREGAR** → la compra muestra `$ 5.000` y `$ 3.000`, total `$ 8.000`.

### Botón AGREGAR

Debe:

1. Tomar el valor actual de la calculadora.
2. Validar que sea válido para agregar (entero mayor que 0).
3. Añadirlo a la lista de compra.
4. Actualizar el total acumulado.
5. Limpiar solo la entrada actual.
6. Mantener intactos los valores previamente agregados.

Si el valor no es válido (vacío o no positivo): no agregar nada (no-op silencioso).

### Botón Borrar

- Elimina un dígito a la vez de la entrada actual.
- No borra la compra.
- No elimina valores ya agregados.

### Botón C

- Limpia completamente la compra (todos los valores agregados).
- Deja la calculadora lista para una nueva entrada.
- No es equivalente a Borrar.
- No cambia el medio de pago seleccionado.

### Botones eliminados

Los botones `+` y `−` no existen en Beta 1.1 y no se reemplazan por otra funcionalidad de operadores.

## Formato monetario

El valor mostrado al usuario debe utilizar pesos colombianos, con el formato ya usado en Beta 1:

```text
1       → $ 1
10      → $ 10
100     → $ 100
1000    → $ 1.000
10000   → $ 10.000
12500   → $ 12.500
5000    → $ 5.000
25000   → $ 25.000
```

El símbolo `$` y los separadores de miles son solamente visuales.

El valor almacenado debe ser un número entero.

La interacción de escritura no debe realizar peticiones HTTP.

## Navegación

- Desde el menú se entra a "Registrar venta".
- Desde "Registrar venta" debe existir un botón para volver al menú.
- Si hay una compra pendiente (valores agregados o entrada en curso), al volver y reentrar se conserva ese estado.
- No se exige diálogo de confirmación al abandonar una compra pendiente en Beta 1.1.

## Medios de pago

Sin cambios respecto a Beta 1:

- Se obtienen desde la base de datos.
- Solo medios activos.
- Selección obligatoria para registrar.

## Registro

Al confirmar y guardar con éxito:

1. Validar nuevamente los datos.
2. Crear la venta con el **total acumulado**.
3. Guardarla localmente vía API.
4. Mostrar popup de venta guardada.
5. Limpiar el estado de entrada y compra.
6. Permanecer en la pantalla "Registrar venta", listo para una nueva venta.

## Ventas confirmadas

Igual que Beta 1:

- No pueden editarse.
- No pueden eliminarse.
- No pueden modificarse.

## Caja y tendero

- caja = 1
- tendero = 1

## Internet

Debe funcionar sin conexión a Internet.

La sincronización con la nube sigue fuera del alcance.

## Fuera del alcance de Beta 1.1

No implementar:

- nombres de productos;
- catálogo de productos;
- cantidades por ítem;
- inventario;
- recetas;
- producción;
- clientes;
- proveedores;
- compras a proveedores;
- usuarios;
- roles;
- login;
- reportes;
- edición o eliminación de ventas;
- tablas o columnas para líneas de detalle de venta;
- endpoints nuevos innecesarios;
- endpoint de calculadora;
- sincronización;
- PostgreSQL funcional;
- decisiones concretas de colores, tipografías o layout visual (ajustes manuales posteriores).

---

# Beta 1 (referencia histórica)

Esta sección describe el alcance original de Beta 1. Sigue siendo la base del sistema; Beta 1.1 la evoluciona en la interfaz de registro.

## Objetivo

Registrar una venta y almacenarla localmente.

## Pantallas (Beta 1)

### Menú principal

- Botón "Registrar venta".

### Registrar venta

- Introducir el valor mediante calculadora numérica.
- Operaciones de suma y resta.
- Limpiar la operación.
- Borrar el último dígito.
- Seleccionar medio de pago.
- Registrar la venta.

### Confirmación

- Valor total y medio de pago.
- Botones "Confirmar" y "No".
- La venta solo se guarda tras "Confirmar".

## Calculadora (Beta 1)

Permitía enteros, `+`, `−`, `C` y borrar último dígito (`⌫`).

Ejemplos válidos de esa versión: `5000`, `5000 + 2000`, `5000 + 2000 - 1000`.

En Beta 1.1 este modelo de operadores queda reemplazado por la lista de compra y el botón AGREGAR.
