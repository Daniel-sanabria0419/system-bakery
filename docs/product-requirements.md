# Product Requirements

## Objetivo general

Crear una aplicación de escritorio para registrar ventas de una panadería.

## Versiones

| Versión | Estado | Objetivo |
|---|---|---|
| Beta 1 | Completada (referencia) | Registrar una venta y almacenarla localmente |
| Beta 1.1 | Completada | Mejorar el flujo de registro con lista de compra en memoria y UX de calculadora |
| Beta 1.2 | En curso | Ajustes estéticos / UX táctil; sin lógica de negocio nueva |

---

# Beta 1.2 (en curso)

## Objetivo

Mejorar la usabilidad táctil y la apariencia del flujo de registro de ventas, sin cambiar qué se guarda ni cómo se calcula. Preserva API y SQLite de Beta 1.1.

## Decisiones (lista cerrada)

1. **Medio de pago:** botón «Seleccionar medio de pago» / «Medio de pago: {nombre}»; popup con botones grandes (máx. 5 por fila); cierra solo al elegir; se puede reabrir para cambiar. Sin `QComboBox`.
2. **Popups confirmar / éxito:** texto y diálogo más grandes; botones ~80 px de alto.
3. **Volver:** ícono de flecha atrás (sin texto); rectángulo un poco más ancho que alto.
4. **Layout registrar venta:** detalle ~1/3, pad ~2/3; scroll en el detalle; solo subir fuente de líneas agregadas.
5. **Menú:** «Registrar venta» arriba a la izquierda, margen ~20 px; color `#2E7D32`. (Pendiente)
6. **Alcance:** solo esos cambios; sin productos, sync, login ni lógica de negocio nueva.

## Estado de implementación

| Etapa | Estado |
|---|---|
| 0 Medio de pago: botón + popup | Hecha |
| 1 Popups confirmar y éxito más grandes | Hecha |
| 2 Botón volver con ícono | Hecha |
| 3 Layout registrar venta | Hecha |
| 4–5 | Pendientes |

Detalle: `docs/beta-1.2/stages.md`. Guía visual: `docs/beta-1.2/visual-guide.md`.

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

No debe contener otras funcionalidades en Beta 1.1.

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
