# Etapas de implementación — Beta 2.0

Documento de referencia de Beta 2.0. **Etapas 0–9 hechas en código; Etapa 10 = documentación de cierre** (este paquete de docs). El cierre formal de la versión queda pendiente del **OK final de Daniel**.

Beta 2.0 introduce productos y ventas con líneas sobre la base Beta 1.2 (UX táctil, capas, SQLite local, dinero en enteros).

## Decisiones arquitectónicas

| # | Decisión | Detalle |
|---|---|---|
| 1 | Categorías | Tabla `categorias` + FK; semilla; **sin CRUD UI** |
| 2 | Snapshot histórico | `venta_lineas` guarda `nombre_producto` y `precio_aplicado` |
| 3 | `POST /ventas` | `{ id_medio_pago, lineas }`; total en backend; sin shape solo-`valor_total` |
| 4 | Calculadora | Búsqueda por precio exacto + rechazo duro sin producto |
| 5 | UI | Productos (CRUD) separado de Registrar venta |
| 6 | Soft-delete | Solo activar/desactivar; no DELETE físico |
| 7 | Legado | Ventas viejas value-only sin backfill de líneas |

## Estado de etapas

| Etapa | Nombre | Estado | PR |
|---|---|---|---|
| 0 | Análisis y diseño (plan en Context) | Hecha | — |
| 1 | Modelo de datos y migración SQLite | Hecha | #10 |
| 2 | Persistencia y servicios productos | Hecha | (vía #11) |
| 3 | APIs productos / categorías | Hecha | #11 |
| 4 | UI CRUD Productos | Hecha | #12 |
| 5 | Compra con líneas (app) | Hecha | #13 |
| 6 | POST /ventas con líneas | Hecha | #14 |
| 7 | UI cobro con productos | Hecha | #15 |
| 8 | Integridad histórica / validaciones | Hecha | #16 |
| 9 | Regresión + smoke | Hecha | #17 |
| 10 | Documentación de cierre | Hecha (pendiente OK final Daniel) | #18 |

## Resumen por etapa

### Etapa 0 — Análisis y diseño

Plan y decisiones en el Context del proyecto (`beta-2-plan.md` / `beta-2-scope.md`). Sin código en el repo.

### Etapa 1 — Modelo de datos

Tablas `categorias`, `productos`, `venta_lineas`; `CREATE TABLE IF NOT EXISTS` + semilla de categorías; ventas/medios existentes intactos. `docs/database.md` actualizado.

### Etapa 2 — Persistencia y app productos

Repositorios y `bakery/app/products.py`: CRUD, listados, búsqueda por precio, soft-delete. Sin HTTP ni Qt.

### Etapa 3 — APIs

Rutas `/categorias`, `/productos`, `/productos/activos`, activar/desactivar; métodos en `ApiClient`. `POST /ventas` aún sin cambiar.

### Etapa 4 — UI Productos

Botón «Productos» en el menú; listar / crear / editar / activar-desactivar.

### Etapa 5 — Compra con líneas (app)

`PurchaseLine` / `SaleDraft`: producto obligatorio, cantidad, subtotales; candidatos por precio exacto. Sin UI de cobro completa aún.

### Etapa 6 — POST /ventas con líneas

Contrato nuevo; snapshot; transacción; rechazo del body antiguo. Cliente y tests actualizados en la misma etapa.

### Etapa 7 — UI cobro

Catálogo en venta, cantidad, búsqueda por precio, lista con nombre/cantidad/subtotal, rechazo sin producto.

### Etapa 8 — Integridad

Validaciones endurecidas; histórico estable ante renombre/precio/desactivación; tests de integridad.

### Etapa 9 — Regresión

Suite completa en verde (**105** pruebas); smoke menú → productos → venta → cobro; `docs/beta-2/regression-notes.md`.

### Etapa 10 — Documentación

Alinear `AGENTS.md`, PRD, architecture, database, sync; este `stages.md`; resumen técnico de cierre en Context.

## Legado value-only

Filas de `ventas` creadas antes de Beta 2 (solo `valor_total`) se conservan **sin** `venta_lineas`. Las ventas nuevas siempre tienen ≥ 1 línea.

## Fuera de alcance (§14)

Historial avanzado, edición de ventas, pedidos/clientes, recetas/inventario/producción, costos/márgenes, múltiples precios/variantes, sync, PostgreSQL, login, reportes.

## Pruebas

- Comando canónico: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`
- Resultado al cierre de Etapa 9: **105 passed**
- Adaptaciones intencionales documentadas en `regression-notes.md` (Agregar, lista, POST, request_count al abrir venta).

## Criterio de cierre (§15)

Cubierto por código + pruebas (Etapas 1–9). Documentación (esta etapa) completa el checklist. **Beta 2.0 se declara cerrada solo con OK final de Daniel.**
