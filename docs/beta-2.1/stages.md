# Etapas de implementación — Beta 2.1

Documento de etapas de **Beta 2.1** (historial, detalle, observaciones, edición ≤ 1 h, auditoría). Plan autoritativo: Context `docs/beta-2.1-plan.md`.

**Estado:** en curso. **Etapas 0–9 hechas** (alcance docs; schema v6; persistencia list/detail + ventana 1 h; API GET; desktop Historial lectura; observaciones durante/posterior + auditoría de creación; `PUT` edición + recalc promo; auditoría completa create/edit + `GET /ventas/{id}/cambios`; desktop edición ≤1 h + obs posterior; regresión 2.0.x + `regression-notes.md`). Etapa 10 pendiente (docs cierre tras OK Daniel).

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

| Etapa | Nombre | Estado | Notas |
|---|---|---|---|
| 0 | Alcance documentado | Hecha | PRD, AGENTS, architecture, database, sync; este `stages.md` |
| 1 | Schema observaciones + auditoría | Hecha | `schema_version` v6; tablas + FKs/CHECKs; `POST /ventas` intacto |
| 2 | Persistencia list/detail/tiempo | Hecha | `list_ventas` / `get_sale_detail` / `sale_is_editable` + insert obs/cambio; reloj inyectable |
| 3 | API lectura GET | Hecha | `GET /ventas`, `GET /ventas/{id}` + `editable` / `es_legado` |
| 4 | Desktop historial + detalle (lectura) | Hecha | Menú Historial; listado + detalle lectura; sin edición/obs |
| 5 | Observaciones durante + posterior | Hecha | `observacion` en POST; `POST /ventas/{id}/observaciones`; `creacion` + `observacion_posterior`; UI confirmar + Agregar |
| 6 | PUT edición + ventana 1 h | Hecha | `PUT /ventas/{id}`; recalc promo; `fecha_venta` inmutable; `edicion` antes/después |
| 7 | Auditoría completa create/edit | Hecha | `creacion`/`edicion` antes/después; `GET /ventas/{id}/cambios`; original conservado |
| 8 | Desktop edición + obs posterior | Hecha | Editar solo si `editable`; obs posterior siempre; sin pad de montos |
| 9 | Regresión Beta 2.0.x | Hecha | Suite offscreen; bordes legado/ventana/carrera; `regression-notes.md` |
| 10 | Docs cierre | Pendiente | Tras OK Daniel |

## Fuera de alcance de Beta 2.1

Pedidos, clientes, recetas, inventario, producción, costos, sync, login, reportes, PostgreSQL, eliminación física de ventas, confiar en reloj del cliente, mutar `fecha_venta`, inventar líneas en legado, motor genérico nuevo de promos, Beta 2.2+.

Detalle: `docs/product-requirements.md` (sección Beta 2.1) y Context `docs/beta-2.1-plan.md` §5.
