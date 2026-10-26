# Beta 2.0 — notas de regresión (Etapa 9)

Suite corrida con `QT_QPA_PLATFORM=offscreen python -m pytest`.

## Resultado

Suite completa en verde (ver PR / commit de Etapa 9). Smoke: menú → Productos → Registrar venta → cobro multi-línea (`tests/test_beta2_smoke.py`).

## Adaptaciones intencionales de pruebas (no son regresiones)

Comportamientos de Beta 1.2 que **cambiaron a propósito** con Beta 2 y cuyas pruebas se reescribieron en etapas 5–7:

| Tema | Antes (1.2) | Ahora (Beta 2) | Dónde se adaptó |
|---|---|---|---|
| Agregar | Monto suelto desde la calculadora | Exige producto seleccionado; rechazo visible | `test_stage2_application`, `test_stage4_desktop`, `test_beta2_desktop_sales` |
| Lista de compra | Solo `format_cop(monto)` | `nombre × cantidad — subtotal` | `test_stage4_desktop`, UI `RegisterSalePage` |
| `POST /ventas` | `{ valor_total, id_medio_pago }` | `{ id_medio_pago, lineas: [...] }` | `test_stage3_api`, client, fakes desktop |
| Abrir registrar venta | Solo carga medios | También carga catálogo (categorías + activos) | Conteos `request_count` en stage4 |
| Producto usado | N/A | Soft-delete; sin DELETE HTTP | `test_beta2_integrity` |

## Checklist §15 (código / pruebas)

Cubierto por la suite (docs de cierre = Etapa 10):

- [x] CRUD productos
- [x] Categorías (asociación / listado / uso en venta)
- [x] Productos seleccionables en venta
- [x] Calculadora como buscador por precio
- [x] No agregar sin producto
- [x] Cantidades / subtotales / total automáticos
- [x] Desactivados fuera de ventas nuevas
- [x] Snapshot histórico
- [x] Pruebas nuevas y anteriores (adaptadas)
- [x] Sin regresiones conocidas en suite
- [ ] Documentación de producto/arquitectura alineada → **Etapa 10**
