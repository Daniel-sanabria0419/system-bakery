# Prioridades táctiles a futuro (no implementar ahora)

Lista de ideas para versiones posteriores. **No son requisitos de Beta 2.0.x.** Documentadas para no olvidar al planificar 2.1+.

Relacionado: [Setup caja + táctil](caja-tactil-setup.md).

---

## Principios

1. Objetivos táctiles ≥ ~48–60 px de alto (dedo).
2. Espacio entre botones para evitar toques dobles.
3. Texto legible a distancia de mostrador (fuente ≥ 16–18 px en chips).
4. Sin depender de hover ni de clic derecho.
5. Flujos cortos: pocos pasos hasta “Pago”.

---

## Mejoras UX / UI (prioridad sugerida)

| Prioridad | Idea | Por qué |
|---|---|---|
| Alta | Revisar métricas globales (pad, Pago, medio, Agregar) contra hits táctiles reales en el local | El pad y cobro se usan más que el CRUD |
| Alta | Feedback visual/háptico claro al tocar (pressed state) en todos los chips | Evita duda “¿registró el toque?” |
| Media | Modo “mostrador”: fuente/contraste más altos (toggle o perfil) | Luz/ambiente del negocio |
| Media | Scroll táctil con inercia y áreas scroll más anchas | Dedo vs trackpad |
| Media | Confirmar / éxito / error siempre con botones ≥ 80 px (ya en 1.2; no regresar) | Ya validado |
| Baja | Teclado virtual solo si hace falta texto (nombres) | Hoy poco texto en cobro |
| Baja | Multi-touch / gestos | Poco valor en POS |

---

## Hardware / integración (futuro, con requisito escrito)

- Abrir caja automática al cobro en Efectivo.
- Impresión de ticket térmico.
- Segundo display “cliente” (total).
- Impedir sleep/screensaver en el PC de caja.

---

## Plataformas

- Seguir priorizando **escritorio + táctil** (PySide6).
- iPad / web / Android solo si hay alcance de producto dedicado (no reutilizar Qt en iOS).

---

## Cómo usar este doc

Al escribir requisitos de una Beta nueva, copiar aquí solo lo que se vaya a construir y moverlo al scope de esa versión. No implementar desde esta lista sin orden de Daniel.
