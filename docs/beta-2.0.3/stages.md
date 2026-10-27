# Etapas de implementación — Beta 2.0.3

Documento de referencia de **Beta 2.0.3** (navegación catálogo Vista A/B + chips más grandes/tipografía editable). Alcance autoritativo y plan detallado viven en el Context del proyecto (`beta-2.0.3-scope.md`, `beta-2.0.3-plan.md`).

**Estado:** etapas 1–3 en `main` (#34–#36); **Beta 2.0.3 cerrada** (OK final de Daniel, 2026-10-27).

Base: Beta 2.0.2 en `main` (wrap, prefijo, panel seleccionado).

## Decisiones (resumen)

| # | Tema | Decisión |
|---|---|---|
| 1 | Vista A | Solo categorías; ningún chip seleccionado (Todos tampoco) |
| 2 | Vista B | Tras categoría o Todos: productos + chip Volver; categorías ocultas |
| 3 | Volver | Chip en la grilla de productos (`PRODUCT_CHIP_*`), no barra aparte; objectName `catalog_back_to_categories` |
| 4 | Métricas | Ancho/alto/fuente editables en `bakery/desktop/style.py` (bloque EDITAR AQUÍ) |
| 5 | Tipografía QSS | Placeholders `__CATEGORY_CHIP_FONT_SIZE__` / `__PRODUCT_CHIP_FONT_SIZE__` vía `load_theme_qss()` |
| 6 | Sin API/SQLite | Solo UX desktop + tests |

## Estado de etapas

| Etapa | Nombre | Estado | PR |
|---|---|---|---|
| 0 | Análisis y diseño (Context) | Hecha | — |
| 1 | Navegación Vista A / Vista B + Volver | Hecha | #34 |
| 2 | Chips más grandes + tipografía en `style.py` | Hecha | #35 |
| 3 | Regresión + docs + cierre Context | Hecha; versión cerrada | #36 |

## Constantes editables (Daniel)

Archivo: `bakery/desktop/style.py`

| Constante | Rol |
|---|---|
| `CATEGORY_CHIP_WIDTH` / `HEIGHT` / `FONT_SIZE` | Chips de categoría |
| `PRODUCT_CHIP_WIDTH` / `HEIGHT` / `FONT_SIZE` | Chips de producto (y Volver) |
| `PRODUCT_CHIP_IMAGE_PADDING` | Separación imagen ↔ texto en el chip |

## Fuera de alcance

Historial de ventas, órdenes, clientes, recetas, inventario, motor genérico de promociones, sync, login, reportes, IA, Beta 2.1+.

## Pruebas

Comando: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`

Casos: `tests/test_beta203_*`. Smoke: `tests/test_beta203_smoke.py`. Notas: `docs/beta-2.0.3/regression-notes.md`.
