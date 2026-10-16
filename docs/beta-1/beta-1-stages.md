# Etapas de implementación — Beta 1

Documento de referencia para implementar Beta 1 por etapas.
Cada etapa termina con pruebas de esa capa antes de pasar a la siguiente.
No implementar funcionalidades fuera del alcance de Beta 1.

Leer también: `AGENTS.md`, `docs/product-requirements.md`, `docs/architecture.md`, `docs/database.md`, `docs/sync.md`.

## Decisiones acordadas

- Dinero como entero (p. ej. `25000`); nunca float ni string `"$ 25.000"`.
- Formato COP solo en UI: `5000` → `$ 5.000`.
- `caja = 1`, `tendero = 1`.
- `id_venta` = UUID en texto, generado al crear la venta (no AUTOINCREMENT).
- Calculadora local: cada tecla actualiza estado en proceso; **sin** FastAPI por tecla.
- FastAPI solo para: `GET /medios-pago` y `POST /ventas` (al confirmar).
- Medios de pago a sembrar (activos): Efectivo, Daviplata, Nequi, Bre-b, Fiado.
- Sin sincronización, PostgreSQL, productos, login, reportes ni edición/eliminación de ventas.

## Estructura de paquetes

```text
bakery/
  desktop/          # PySide6 + cliente HTTP
  api/              # FastAPI (rutas delgadas)
  app/              # lógica de registro; calculadora local (usada por desktop, no por HTTP)
  persistence/      # SQLite, schema, repositorios
tests/
requirements.txt
```

## Estado

Beta 1 está completada como base funcional (registro de ventas con calculadora de expresión `+`/`−`). La evolución del flujo de registro continúa en **Beta 1.1**: ver `docs/beta-1.1/stages.md` y el plan en `docs/beta-1.1/`.

| Etapa | Nombre | Estado |
|---|---|---|
| 0 | Entorno | Hecha |
| 1 | Persistencia | Hecha |
| 2 | Lógica de aplicación | Hecha |
| 3 | FastAPI | Hecha |
| 4 | Desktop | Hecha |
| 5 | Integración y cierre | Hecha (arranque unificado uvicorn + Qt) |

---

### Etapa 0 — Entorno

- `requirements.txt`: PySide6, FastAPI, uvicorn, httpx, pytest, pytest-qt
- Paquete `bakery/` con `__init__.py` vacíos
- Punto de entrada: `python -m bakery.desktop` (o script equivalente)
- Arranque preparado de PySide6 + FastAPI (sin lógica de negocio)

### Etapa 1 — Persistencia

- Conexión SQLite, schema, seed de medios
- Repositorio: listar medios activos; insertar venta con `id_venta` UUID TEXT
- Tests: constraints (valor ≤ 0, FK inválida); seed

### Etapa 2 — Lógica de aplicación

- Calculadora local (enteros, +/−, C, ⌫, rechazo de casos del PRD); tests sin Qt ni HTTP
- Caso de uso “registrar venta”: generar UUID, validar valor y medio activo, asignar caja/tendero/fecha
- Formato COP como función de presentación usada por UI (y tests de formato); no se usa al persistir
- Alinear `docs/database.md`: `id_venta` UUID, no entero incremental

### Etapa 3 — FastAPI

- App factory: `GET /medios-pago` y `POST /ventas` solamente
- Sin endpoint de calculadora
- Tests con `TestClient` (medios, venta ok con UUID en respuesta/BD, venta 0, medio inactivo)

### Etapa 4 — Desktop

- Cliente HTTP local: GET medios y POST venta; **cero llamadas** al pulsar teclas de la calculadora
- Tres superficies (menú, registro, diálogo)
- Al abrir registrar venta: cargar medios
- Tras confirmar: POST venta, reset de calculadora y selección, volver a la misma pantalla de registro
- Tests pytest-qt del flujo feliz y de bloqueo de registro inválido (sin guardar)

### Etapa 5 — Integración y cierre

- Arranque unificado (hilo uvicorn + Qt)
- Prueba de humo: proceso abre, registra una venta, fila en SQLite
- Verificar que no hay endpoints ni pantallas fuera de alcance
