# Etapas de implementación — Beta 2.1

Documento de referencia de **Beta 2.1** (historial, detalle, observaciones, edición ≤ 1 h, auditoría). Plan autoritativo: Context `docs/beta-2.1-plan.md`. Informe de cierre: Context `docs/beta-2.1-closure.md`.

**Estado:** etapas 0–10 hechas en código/docs. El cierre formal de la versión queda pendiente del **OK final de Daniel**.

Preservar Beta 2.0.x. Comando canónico de pruebas:  
`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`

## Decisiones (CLOSED en el plan)

| # | Tema | Decisión |
|---|---|---|
| 1 | Reloj ventana 1 h | Solo backend (`datetime.now()` del proceso API local); UI countdown informativo |
| 2 | Create vs edit | `POST /ventas` = create idempotente; `PUT /ventas/{id}` = editar |
| 3 | Observaciones | Tabla append-only; orígenes `durante_venta` / `posterior`; posterior siempre permitido |
| 4 | Auditoría | `venta_cambios` con `antes_json` / `despues_json`; creación deja rastro |
| 5 | Legado value-only | Historial/detalle sí; no inventar líneas; edición de líneas no aplica |
| 6 | Promo al editar | Misma ruta que `register_sale` (catálogo vigente); producto inactivo rechazado |

## Estado de etapas

| Etapa | Nombre | Estado | PR |
|---|---|---|---|
| 0 | Alcance documentado | Hecha | #67 |
| 1 | Schema observaciones + auditoría | Hecha | #68 |
| 2 | Persistencia list/detail/tiempo | Hecha | #69 |
| 3 | API lectura GET | Hecha | #70 |
| 4 | Desktop historial + detalle (lectura) | Hecha | #71 |
| 5 | Observaciones durante + posterior | Hecha | #72 |
| 6 | PUT edición + ventana 1 h | Hecha | #73 |
| 7 | Auditoría completa create/edit | Hecha | #74 |
| 8 | Desktop edición + obs posterior | Hecha | #75 |
| 9 | Regresión Beta 2.0.x | Hecha | #76 |
| 10 | Docs cierre | Hecha (pendiente OK final Daniel) | #77 |

## Resumen por etapa

### Etapa 0 — Alcance documentado

PRD, `AGENTS.md`, architecture, database, sync; este `stages.md`. Sin código de app.

### Etapa 1 — Schema

`schema_version` v6: tablas `venta_observaciones` y `venta_cambios` (FKs/CHECKs). `POST /ventas` intacto.

### Etapa 2 — Persistencia

`list_ventas`, `get_sale_detail`, `sale_is_editable` (`elapsed < 3600`), insert obs/cambio; reloj inyectable.

### Etapa 3 — API lectura

`GET /ventas`, `GET /ventas/{id}` con `editable` / `es_legado` calculados en servidor.

### Etapa 4 — Desktop lectura

Menú **Historial**; listado + detalle; sin edición aún.

### Etapa 5 — Observaciones

`observacion` opcional en `POST /ventas`; `POST /ventas/{id}/observaciones`; auditoría `creacion` / `observacion_posterior`; UI confirmar + Agregar.

### Etapa 6 — Edición backend

`PUT /ventas/{id}` dentro de 1 h; recalc promo; `fecha_venta` inmutable; legado sin inventar líneas; `edicion` antes/después.

### Etapa 7 — Auditoría completa

`creacion`/`edicion` con JSON; `GET /ventas/{id}/cambios`; original conservado.

### Etapa 8 — Desktop edición

Editar solo si `editable`; obs posterior siempre; sin pad de montos sueltos.

### Etapa 9 — Regresión

Suite offscreen verde; bordes legado / ventana exacta / carrera POST; `docs/beta-2.1/regression-notes.md`.

### Etapa 10 — Documentación

Alinear `AGENTS.md`, PRD, architecture, database, sync; este `stages.md` + `regression-notes.md`; informe técnico en Context `docs/beta-2.1-closure.md`.

## Rutas API (cierre)

| Método | Ruta | Rol |
|---|---|---|
| `POST` | `/ventas` | Create idempotente (+ `observacion` opcional) |
| `GET` | `/ventas` | Listado + `editable` / `es_legado` |
| `GET` | `/ventas/{id}` | Detalle + líneas + obs + flags |
| `GET` | `/ventas/{id}/cambios` | Auditoría |
| `PUT` | `/ventas/{id}` | Edición ≤ 1 h (409 fuera de ventana) |
| `POST` | `/ventas/{id}/observaciones` | Observación posterior (siempre) |

## Fuera de alcance de Beta 2.1

Pedidos, clientes, recetas, inventario, producción, costos, sync, login, reportes, PostgreSQL, eliminación física de ventas, confiar en reloj del cliente, mutar `fecha_venta`, inventar líneas en legado, motor genérico nuevo de promos, Beta 2.2+.

Detalle: `docs/product-requirements.md` (sección Beta 2.1) y Context `docs/beta-2.1-plan.md` §5.

## Pruebas

- Comando canónico: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`
- Resultado al cierre de Etapa 9: **364 passed** (ver `regression-notes.md`)

## Criterio de cierre

Cubierto por código + pruebas (Etapas 1–9) y documentación (esta etapa). **Beta 2.1 se declara Terminada solo con OK final de Daniel.**
