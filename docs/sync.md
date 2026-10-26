# Synchronization

## Estado

La sincronización con la base de datos en la nube está **FUERA DEL ALCANCE**.

Esto incluye Beta 1, Beta 1.1, Beta 1.2 y **Beta 2.0**.

## Comportamiento actual

Las ventas (y el catálogo de productos) se almacenan únicamente en SQLite local.

**Beta 2.0 no introduce ni modifica ningún comportamiento de sincronización.** Añade tablas locales (`categorias`, `productos`, `venta_lineas`) y cambia el contrato local de `POST /ventas`; todo sigue offline.

No se debe implementar:

- conexión con PostgreSQL;
- subida automática de ventas o productos;
- sincronización manual;
- cola de sincronización;
- resolución de conflictos;
- reintentos de sincronización;
- estados de sincronización;
- servicios cloud.

## Objetivo futuro

En una versión posterior se implementará un mecanismo para sincronizar los datos locales con una base de datos PostgreSQL ubicada en la nube.

La sincronización deberá diseñarse teniendo en cuenta:

- funcionamiento offline;
- identificadores únicos generados localmente;
- posibilidad de múltiples dispositivos;
- prevención de duplicados;
- reintentos;
- integridad de los datos (incluidas líneas con snapshot).

Estas decisiones se definirán cuando se diseñe esa versión.

## Regla

El agente NO debe implementar ninguna parte del sistema de sincronización durante las betas documentadas, incluida Beta 2.0.
