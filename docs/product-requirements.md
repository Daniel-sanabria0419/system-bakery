# Product Requirements — Beta 1

## Objetivo

Crear una aplicación de escritorio para registrar ventas de una panadería.

Beta 1 tendrá únicamente la funcionalidad necesaria para registrar una venta y almacenarla localmente.

## Pantallas

### 1. Menú principal

Debe mostrar:

- Botón "Registrar venta".

No debe contener otras funcionalidades en Beta 1.

### 2. Registrar venta

Debe permitir:

- Introducir el valor mediante una calculadora numérica.
- Realizar operaciones de suma y resta.
- Limpiar la operación.
- Borrar el último dígito.
- Seleccionar un medio de pago.
- Registrar la venta.

### 3. Confirmación

Al presionar "Registrar venta", debe aparecer una confirmación.

Debe mostrar:

- Valor total.
- Medio de pago seleccionado.

Debe contener:

- Botón "Confirmar".
- Botón "No".

La venta solamente se guarda después de presionar "Confirmar".

## Calculadora

La calculadora debe permitir:

- Números enteros.
- Suma (+).
- Resta (-).
- Limpiar (C).
- Borrar último dígito (⌫).

No debe permitir:

- División.
- Decimales.
- Números negativos.
- Operadores consecutivos.
- Operaciones incompletas.
- Registrar una venta con valor 0.
- Registrar una venta sin valor.

Toda operación debe terminar en un número entero válido.

Ejemplos válidos:

5000
5000 + 2000
5000 + 2000 - 1000

Ejemplos inválidos:

5000 +
5000 -
5000 + 2000 -
5000 - 6000

## Formato monetario

El valor mostrado al usuario debe utilizar pesos colombianos.

Ejemplos:

5000 → $ 5.000
25000 → $ 25.000
1250000 → $ 1.250.000

El símbolo `$` y los separadores de miles son solamente visuales.

El valor almacenado debe ser un número entero.

## Medios de pago

Los medios de pago deben obtenerse desde la base de datos.

Solo deben mostrarse medios de pago activos.

El usuario debe seleccionar obligatoriamente un medio de pago.

## Registro

Al confirmar:

1. Validar nuevamente los datos.
2. Crear la venta.
3. Guardarla localmente.
4. Limpiar el estado actual.
5. Regresar a la pantalla "Registrar venta".

## Ventas confirmadas

En Beta 1 una venta confirmada:

- No puede editarse.
- No puede eliminarse.
- No puede modificarse.

La corrección de errores se estudiará en una versión futura.

## Caja y tendero

En Beta 1:

- caja = 1
- tendero = 1

No existe todavía administración de cajas ni tenderos.

## Internet

Beta 1 debe funcionar sin conexión a Internet.

La sincronización con una base de datos en la nube está fuera del alcance de Beta 1.

## Fuera del alcance

No implementar:

- productos;
- inventario;
- recetas;
- producción;
- clientes;
- proveedores;
- compras;
- usuarios;
- roles;
- login;
- reportes;
- edición;
- eliminación;
- sincronización;
- PostgreSQL funcional.