# AGENTS.md

## Propósito del proyecto

Este proyecto es una aplicación de escritorio para una panadería.

La primera versión del proyecto es una Beta cuyo único objetivo funcional es registrar ventas.

El objetivo de esta Beta es validar la arquitectura, la experiencia de usuario y el flujo básico de registro de ventas antes de agregar funcionalidades adicionales.

## Alcance de Beta 1

La Beta 1 solamente debe permitir:

1. Abrir la aplicación.
2. Entrar a "Registrar venta".
3. Calcular el valor de una venta mediante una calculadora.
4. Seleccionar un medio de pago.
5. Confirmar el registro.
6. Guardar la venta localmente en SQLite.
7. Volver a la pantalla de registro después de guardar.

## Fuera del alcance

NO implementar en Beta 1:

- Productos.
- Inventario.
- Recetas.
- Producción.
- Clientes.
- Proveedores.
- Compras.
- Usuarios.
- Roles.
- Login.
- Reportes.
- Edición de ventas.
- Eliminación de ventas.
- Corrección de ventas.
- Sincronización con la nube.
- PostgreSQL funcional.
- IA dentro de la aplicación.
- Funcionalidades no especificadas en los documentos de requisitos.

Si una funcionalidad no está especificada y no es necesaria para que Beta 1 funcione, NO debe implementarse.

## Stack

Frontend:
- Python
- PySide6 / Qt

Backend local:
- Python
- FastAPI

Base de datos local:
- SQLite

Base de datos futura:
- PostgreSQL

Control de versiones:
- Git
- GitHub

Testing:
- pytest
- pytest-qt cuando sea necesario para pruebas de interfaz.

IDE / agente:
- Cursor
- Cursor Agent

## Principios de arquitectura

- La interfaz gráfica no debe contener lógica de negocio.
- La lógica de negocio debe estar separada de la interfaz.
- El acceso a datos debe estar separado de la lógica de negocio.
- La aplicación debe poder funcionar completamente sin Internet.
- No utilizar floats para representar dinero.
- Las ventas deben tener identificadores únicos.
- Mantener el código simple y proporcional al alcance de Beta 1.
- No introducir abstracciones innecesarias.
- No implementar funcionalidades futuras anticipadamente.

## Forma de trabajo

Antes de realizar cambios importantes:

1. Revisar los documentos de `docs/`.
2. Entender el alcance actual.
3. Identificar qué archivos serán modificados.
4. Implementar el cambio de forma incremental.
5. Ejecutar las pruebas correspondientes.
6. No continuar agregando funcionalidades no solicitadas.

## Regla principal

El agente debe priorizar:

- simplicidad;
- claridad;
- mantenibilidad;
- pruebas;
- separación de responsabilidades;
- cumplimiento exacto del alcance.

No se debe optimizar para construir muchas funcionalidades.

Se debe optimizar para construir correctamente una Beta pequeña y funcional.