# Setup recomendado — caja + pantalla táctil

**Producto:** POS panadería (Python / PySide6). Corre en **macOS / Windows / Linux**, no en iPad nativo.

**Fecha:** 2026-10-27. Orientativo; no es un requisito de Beta vigente.

Relacionado: [Prioridades táctiles a futuro](tactil-prioridades-futuro.md).

---

## Objetivo

Puesto de cobro en el local: pantalla táctil grande, caja de dinero, PC pequeño que ejecute la app ya construida.

---

## Hardware sugerido (mínimo viable)

| Pieza | Rol | Notas |
|---|---|---|
| Mini PC o Mac mini / NUC | Corre la app y SQLite local | Preferir el mismo OS que usas en desarrollo (Mac) para menos fricción |
| Monitor táctil 15–22" | Interacción principal | Capacitive; buena lectura a ~arm’s length; montaje VESA o soporte |
| Caja de dinero (cash drawer) | Efectivo | USB o RJ11 vía impresora térmica; apertura por software o botón |
| (Opcional) Impresora térmica 58/80 mm | Recibos | Más adelante; no bloquea Beta actual |
| (Opcional) Lector de códigos | Futuro catálogo | Fuera de alcance hoy |

**No usar el iPad como host** de la app PySide6. Si hace falta ver/tocar desde el iPad, solo como cliente remoto (Sidecar / VNC) hacia el Mac/PC.

---

## Layout físico sugerido

1. Pantalla táctil frente al tendero (ángulo ~15–30°).
2. Caja debajo o al lado del mostrador, al alcance de la mano dominante.
3. Teclado/mouse de respaldo (arranque, mantenimiento, fallos táctiles).
4. Cableado fijo (alimentación + USB); evitar hubs inestables.

---

## Software

1. Instalar Python + dependencias (`requirements.txt`) en el PC de caja.
2. Carpeta de datos con `data/bakery.sqlite3` en disco local (offline).
3. Arranque: `python3 -m bakery.desktop` (o acceso directo / LaunchAgent en Mac).
4. Probar: menú → Productos → Registrar venta → cobro completo.
5. Backup periódico del SQLite (USB o copia a otro disco).

---

## Caja de dinero

- Conectar según el modelo (USB directo o vía impresora).
- En esta Beta **no hay** comando de apertura de caja en la app; usar botón físico o driver del fabricante.
- A futuro: evaluar “abrir caja al confirmar venta en Efectivo” (requiere requisito explícito).

---

## Prueba en el negocio (checklist)

- [ ] App abre sin Internet.
- [ ] Chips de categoría/producto se tocan sin miss-clicks.
- [ ] Pad numérico usable con dedo.
- [ ] Popups confirmar/éxito/medio tienen botones grandes.
- [ ] Flujo Pan pequeño (valor → cantidad) usable de pie.
- [ ] Caja abre (manual) y cierra bien en el mostrador.

---

## Coste / alternativas

- **Barato:** PC usado + monitor táctil USB.
- **Mac-first:** Mac mini + monitor táctil compatible.
- **Temporal:** MacBook en el mostrador + trackpad/teclado hasta comprar táctil.
