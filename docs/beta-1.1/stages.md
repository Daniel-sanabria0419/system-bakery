# Etapas de implementación — Beta 1.1

Documento de referencia para implementar Beta 1.1 por etapas.
Cada etapa termina con pruebas verificables antes de pasar a la siguiente.
No implementar funcionalidades fuera del alcance de Beta 1.1.

Leer también: `AGENTS.md`, `docs/product-requirements.md`, `docs/architecture.md`, `docs/database.md`, `docs/sync.md`, y el plan en `docs/beta-1.1/`.

## Decisiones acordadas

- Lista de compra en memoria; sin cambios de esquema SQLite.
- Separación: entrada actual ≠ líneas de compra ≠ total.
- Sin botones `+` / `−`; botón **AGREGAR**.
- **Borrar** = un dígito de la entrada; **C** = limpiar compra + entrada.
- Formato COP existente: `5000` → `$ 5.000` (sin cambiar el contrato de `format_cop`).
- Calculadora local; HTTP solo al cargar medios y al confirmar venta.
- `POST /ventas` sin cambios de contrato: `{ valor_total, id_medio_pago }` con el total acumulado.
- AGREGAR con valor inválido: no-op silencioso.
- Volver al menú conserva el estado de compra/entrada.
- Popup de éxito solo tras POST exitoso.
- Sin sync, productos, catálogo, cantidades ni líneas persistidas.

## Estado

| Etapa | Nombre | Estado |
|---|---|---|
| 0 | Documentación | Hecha |
| 1 | Modelo Entry + Purchase | Hecha |
| 2 | Formato monetario en tiempo real | Hecha |
| 3 | UI pad, AGREGAR, Borrar, C, vista Compra | Hecha |
| 4 | Navegación Volver | Hecha |
| 5 | Popup venta guardada | Hecha |
| 6 | Preparación visual | Hecha |
| 7 | Regresión completa | Pendiente |

El detalle de objetivos, archivos, pruebas y criterios de aceptación está en el plan de desarrollo de Beta 1.1.
