# AGENTS.md

## Propósito del proyecto

Este proyecto es una aplicación de escritorio para una panadería.

La primera versión del proyecto es una Beta cuyo único objetivo funcional es registrar ventas.

El objetivo de esta Beta es validar la arquitectura, la experiencia de usuario y el flujo básico de registro de ventas antes de agregar funcionalidades adicionales.

## Alcance de Beta 1

La Beta 1 (completada como base) solamente debía permitir:

1. Abrir la aplicación.
2. Entrar a "Registrar venta".
3. Calcular el valor de una venta mediante una calculadora.
4. Seleccionar un medio de pago.
5. Confirmar el registro.
6. Guardar la venta localmente en SQLite.
7. Volver a la pantalla de registro después de guardar.

## Beta 1.1

**Beta 1.1 está terminada.** Cubre la lista de compra en memoria, la interacción de la calculadora, el popup de éxito y la navegación atrás. Las etapas 0 a 7 están hechas; la etapa 7 es la regresión completa.

Requisitos y arquitectura:

- `docs/product-requirements.md`
- `docs/architecture.md`
- `docs/database.md`
- `docs/sync.md`
- `docs/beta-1.1/stages.md`

Preservar lo que ya funciona de Beta 1 y de Beta 1.1.

## Beta 1.2

**Beta 1.2 está terminada.** Solo cambios estéticos / UX táctil sobre 1.1. Sin lógica de negocio nueva; mismos contratos API y SQLite. Etapas 0–5 hechas; la etapa 5 cerró la regresión (67 pruebas en verde).

Alcance implementado:

1. Medio de pago: botón + popup (sin `QComboBox`).
2. Popups confirmar / éxito más grandes (botones ~80 px).
3. Botón volver con flecha `←` (sin texto «Volver»).
4. Layout registrar venta: detalle ~1/3, pad ~2/3, scroll, fuente solo en líneas.
5. Menú: «Registrar venta» arriba-izquierda, margen ~20 px, color `#2E7D32`.

Requisitos y etapas:

- `docs/product-requirements.md` (sección Beta 1.2)
- `docs/architecture.md`
- `docs/beta-1.2/stages.md`
- `docs/beta-1.2/visual-guide.md`

Preservar lo que ya funciona de Beta 1, 1.1 y 1.2.

Beta 2 no tiene requisitos: Daniel todavía no los ha planteado. No implementar una versión siguiente hasta que esté escrita en los documentos.

## Fuera del alcance

NO implementar, ni anticipar en una versión que todavía no está especificada:

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

Si una funcionalidad no está especificada en los documentos de requisitos, NO debe implementarse.

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
- Mantener el código simple y proporcional al alcance especificado.
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

## Cursor Cloud specific instructions

Las dependencias de Python se instalan con `python3 -m pip install --user -r requirements.txt`. PySide6 además necesita bibliotecas de sistema (libEGL y XCB); el entorno ya las instala.

- Pruebas: `python3 -m pytest` desde la raíz del repositorio. Sin pantalla, usar `QT_QPA_PLATFORM=offscreen python3 -m pytest`.
- Aplicación: `python3 -m bakery.desktop`. Arranca la ventana y la API local en `http://127.0.0.1:8765`. La base SQLite queda en `data/bakery.sqlite3`.
- No hay un servidor que deba quedar en marcha por separado: la ventana inicia uvicorn en un hilo.
