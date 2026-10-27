# Etapas de implementación — Beta 2.0.2

Documento de referencia de **Beta 2.0.2** (layout cobro, filtro por prefijo de precio, listado Productos blanco). Alcance autoritativo y plan detallado viven en el Context del proyecto (`beta-2.0.2-scope.md`, `beta-2.0.2-plan.md`).

**Estado:** etapas 1–6 en código (PRs #28–#33); **pendiente OK final de Daniel** para declarar la versión cerrada.

Base: Beta 2.0.1 en `main` (Pan pequeño, chips, imágenes).

## Decisiones (resumen)

| # | Tema | Decisión |
|---|---|---|
| 1 | Prefijo | `str(precio).startswith(digits)` vía `Calculator.digits()`; vacío → sin filtro de precio |
| 2 | Alcance | Prefijo solo sin producto seleccionado; acotado a categoría activa (Todos = todas) |
| 3 | Modos pad | Sin selección → prefijo; Pan pequeño → valor→cantidad; otro → solo cantidad/`+/-` |
| 4 | UI búsqueda | Sin bloque «Búsqueda por precio»; filtro en la grilla de productos |
| 5 | Layout | Wrap por ancho (~6 de referencia, no fijo); fondos `#d7d4ce`; divisor negro |
| 6 | Panel | Imagen, nombre, unitario + subtotal; qty (número) luego −/+ |
| 7 | Productos CRUD | Fondo listado `#FFFFFF`; `payment-method-button` intacto |

## Estado de etapas

| Etapa | Nombre | Estado | PR |
|---|---|---|---|
| 0 | Análisis y diseño (Context) | Hecha | — |
| 1 | Filtro prefijo (app) | Hecha | #28 |
| 2 | Quitar UI búsqueda; cablear modos | Hecha | #29 |
| 3 | Wrap + `#d7d4ce` + divisor | Hecha | #30 |
| 4 | Panel producto seleccionado | Hecha | #31 |
| 5 | Fondo blanco listado Productos | Hecha | #32 |
| 6 | Regresión + docs | Hecha (este PR); pendiente OK final | #33 |

## Fuera de alcance

Historial de ventas, órdenes, clientes, recetas, inventario, motor genérico de promociones, sync, login, reportes, IA, Beta 2.1+.

## Pruebas

Comando: `QT_QPA_PLATFORM=offscreen python3 -m pytest --import-mode=importlib`

Casos: `tests/test_beta202_*`. Smoke: `tests/test_beta202_smoke.py`. Notas: `docs/beta-2.0.2/regression-notes.md`.
