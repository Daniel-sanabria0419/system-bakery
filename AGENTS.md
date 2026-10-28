# AGENTS.md

## Propósito del proyecto

Este proyecto es una aplicación de escritorio para una panadería.

La primera versión del proyecto es una Beta cuyo objetivo funcional inicial fue registrar ventas. Con **Beta 2.0** el registro pasa a basarse en **productos** (catálogo + líneas de venta), manteniendo el flujo offline local.

El objetivo de las betas es validar arquitectura, experiencia de usuario y el flujo de registro de ventas antes de agregar funcionalidades adicionales no especificadas.

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

**Beta 1.2 está terminada.** Solo cambios estéticos / UX táctil sobre 1.1. Sin lógica de negocio nueva en su momento; mismos contratos API y SQLite de entonces. Etapas 0–5 hechas; la etapa 5 cerró la regresión (67 pruebas en verde).

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

Preservar lo que ya funciona de Beta 1, 1.1 y 1.2 (salvo lo que Beta 2 cambia a propósito).

## Beta 2.0

**Beta 2.0 está implementada en código** (etapas 1–9; documentación de cierre = etapa 10). Introduce productos y ventas con líneas.

Alcance implementado:

1. Catálogo: categorías (semilla, sin CRUD UI) y productos (CRUD + activar/desactivar).
2. Menú: botón «Productos» además de «Registrar venta».
3. Venta: selección por categoría, cantidad, calculadora como filtro de catálogo (en 2.0 era precio exacto; desde 2.0.2 es **prefijo** de precio en la grilla).
4. No se agrega línea sin producto seleccionado (rechazo visible).
5. `POST /ventas` con `id_medio_pago` + `lineas`; total calculado en backend.
6. Snapshot histórico en `venta_lineas` (`nombre_producto`, `precio_aplicado`).
7. Soft-delete de productos; desactivados fuera de ventas nuevas.
8. Ventas antiguas solo-`valor_total` se conservan sin líneas (legado value-only).

Requisitos y etapas:

- `docs/product-requirements.md` (sección Beta 2.0)
- `docs/architecture.md`
- `docs/database.md`
- `docs/beta-2/stages.md`
- `docs/beta-2/regression-notes.md`

No implementar una versión siguiente (Beta 3+) hasta que esté escrita en los documentos de requisitos.

## Beta 2.0.1

**Beta 2.0.1 está terminada** (etapas 1–8 en main vía #19–#26; OK final de Daniel 2026-10-26). Extiende Beta 2.0 con Pan pequeño y pulido de catálogo/imágenes/formularios.

Alcance implementado:

1. Categoría «Pan pequeño» (por nombre); precio unitario $300; promo automática 7 / $2000 **solo si la cantidad es múltiplo exacto de 7** (sin flag por producto; sin “grupos + resto”).
2. Módulo central de precios (`pan_pequeno_pricing`): cantidades enteras, ceil hacia arriba.
3. En cobro: calculadora por **valor** para Pan pequeño; otras categorías por unidades (Beta 2.0.2 reemplaza la búsqueda exacta por prefijo en grilla).
4. Chips de catálogo (Todos primero; métricas/color del scope); fondo de lista no negro.
5. Imágenes de producto (`ruta_imagen`, carpeta `imagenes/productos/`); categorías por convención de archivo.
6. Crear / Editar producto con el mismo lenguaje visual (placeholders/selects).

Requisitos y etapas:

- `docs/product-requirements.md` (sección Beta 2.0.1)
- `docs/architecture.md`
- `docs/database.md`
- `docs/beta-2.0.1/stages.md`
- `docs/beta-2.0.1/regression-notes.md`

Preservar Beta 2.0. **No** motor genérico de promociones ni features de Beta 2.1+.

## Beta 2.0.2

**Beta 2.0.2 está terminada** (etapas 1–6 en main vía #28–#33; OK final de Daniel 2026-10-27). Solo UX/layout y filtro de catálogo sobre 2.0.1.

Alcance implementado:

1. Prefijo de precio (`candidates_by_price_prefix`) sobre el string del entero; solo sin producto seleccionado; acotado a la categoría activa (Todos = todas).
2. Sin UI «Búsqueda por precio»; dígitos filtran la grilla de productos.
3. Con producto: Pan pequeño = valor→cantidad; resto = cantidad/`+/-` (sin prefijo).
4. Catálogo: wrap por ancho (~6 de referencia); fondos `#d7d4ce`; divisor negro entre categorías y productos.
5. Panel seleccionado: imagen, nombre, unitario + subtotal; cantidad luego −/+.
6. Listado Productos (CRUD): fondo blanco (`#FFFFFF`).

Requisitos y etapas:

- `docs/product-requirements.md` (sección Beta 2.0.2)
- `docs/architecture.md`
- `docs/beta-2.0.2/stages.md`
- `docs/beta-2.0.2/regression-notes.md`

Preservar Beta 2.0.1. **No** features de Beta 2.1+.

## Beta 2.0.3

**Beta 2.0.3 está terminada** (etapas 1–3 en main vía #34–#36; OK final de Daniel 2026-10-27). Solo UX de navegación de catálogo y métricas de chips sobre 2.0.2.

Alcance implementado:

1. Vista A (solo categorías, sin selección visual) / Vista B (productos + chip Volver).
2. Chips más grandes (métricas vigentes en `style.py`: 135×120); tipografía y tamaños editables en `bakery/desktop/style.py`.

Requisitos y etapas:

- `docs/product-requirements.md` (sección Beta 2.0.3)
- `docs/architecture.md`
- `docs/beta-2.0.3/stages.md`
- `docs/beta-2.0.3/regression-notes.md`

Ops / backlog táctil (no implementar sin requisito): `docs/caja-tactil-setup.md`, `docs/tactil-prioridades-futuro.md`.

Preservar Beta 2.0.2. **No** features de Beta 2.1+.

## Beta 2.0.4

**Beta 2.0.4 está terminada** (etapas 1–7 en main vía #39–#44; OK final de Daniel 2026-10-27). Migra la promo hardcodeada de Pan pequeño hacia `promociones` + FK, con agrupación de carrito.

Alcance implementado:

1. Schema/seed/dual-path/UI/cutover (#39–#43).
2. `USE_PROMOCIONES_TABLE` default **True**; cobro por FK/grupo (`cantidad_por_monto`).
3. Snapshot `venta_lineas.id_promocion` / `nombre_promocion` (schema v3) (#44).
4. `pan_pequeno_pricing` = shim; docs: `docs/beta-2.0.4/stages.md`, `regression-notes.md`.

Requisitos y etapas:

- `docs/product-requirements.md` (sección Beta 2.0.4)
- `docs/database.md`
- `docs/beta-2.0.4/stages.md`
- Plan / cierre Context: `docs/beta-2.0.4-promociones-plan.md`, `docs/beta-2.0.4-closure.md`

Preservar Beta 2.0.4.

## Beta 2.0.5

**Cobro por nudos de la tabla ceil** (miles, sin tope). Fuera de esos nudos: `cantidad × precio_base`.

Alcance:

1. Nudos: 4→1000, 7→2000, …, 34→10000, 37→11000, 40→12000 (sigue en miles).
2. Resto: 1→300, 8→2400, 12→3600. Cada línea se cobra sola (17 + 5 → 5000 + 1500). Sin pool de carrito.
3. JSON DB slim: `{"precio_base":300,"modo":"ceil"}`; G/M/política greedy en defaults de código.
4. `modo: ceil` = valor→qty sin cambio.

Requisitos y etapas:

- `docs/product-requirements.md` (sección Beta 2.0.5)
- `docs/beta-2.0.5/stages.md`
- Diseño Context: `docs/beta-2.0.5-promo-por-producto-y-grupo.md`

Preservar Beta 2.0.5. **No** features de Beta 2.1+ hasta que estén en los requisitos.

## Fuera del alcance

NO implementar, ni anticipar en una versión que todavía no está especificada:

- Inventario / stock.
- Recetas / ingredientes / costos / márgenes.
- Producción.
- Clientes / pedidos.
- Proveedores / compras a proveedores.
- Usuarios / roles / login.
- Reportes.
- Historial avanzado de ventas.
- Edición / eliminación / corrección de ventas.
- Múltiples precios o variantes de producto.
- CRUD de categorías en UI (en Beta 2 solo semilla + listado).
- Sincronización con la nube.
- PostgreSQL funcional.
- IA dentro de la aplicación.
- Funcionalidades no especificadas en los documentos de requisitos.

**Nota:** el catálogo de **productos** y las **líneas de venta** sí están en alcance de Beta 2.0 (ver sección anterior). Lo demás de la lista histórica sigue fuera.

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

Preferir el venv del repo (`.venv`) para dependencias y pruebas. Si no existe: `python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt`. Alternativa cloud sin venv: `python3 -m pip install --user -r requirements.txt`. PySide6 además necesita bibliotecas de sistema (libEGL y XCB); el entorno cloud ya las instala.

- **Pruebas (comando canónico):** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` desde la raíz. Evitar `python3 -m pytest` sin venv: en algunas Mac un paquete `tests` en site-packages sombrea `./tests` y la suite no se recolecta bien.
- Aplicación: `.venv/bin/python -m bakery.desktop` (o `python3 -m bakery.desktop`). Arranca la ventana y la API local en `http://127.0.0.1:8765`. La base SQLite queda en `data/bakery.sqlite3`.
- Puerto fijo `8765`: una segunda instancia puede fallar al bindear si la primera sigue viva. Ver `docs/caja-tactil-setup.md`.
- No hay un servidor que deba quedar en marcha por separado: la ventana inicia uvicorn en un hilo.
