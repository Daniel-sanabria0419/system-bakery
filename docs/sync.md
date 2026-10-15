# Synchronization

## Estado

La sincronización con la base de datos en la nube está FUERA DEL ALCANCE de Beta 1.

## Beta 1

Las ventas se almacenan únicamente en SQLite local.

No se debe implementar:

- conexión con PostgreSQL;
- subida automática de ventas;
- sincronización manual;
- cola de sincronización;
- resolución de conflictos;
- reintentos de sincronización;
- estados de sincronización;
- servicios cloud.

## Objetivo futuro

En una versión posterior se implementará un mecanismo para sincronizar las ventas locales con una base de datos PostgreSQL ubicada en la nube.

La sincronización deberá diseñarse teniendo en cuenta:

- funcionamiento offline;
- identificadores únicos generados localmente;
- posibilidad de múltiples dispositivos;
- prevención de duplicados;
- reintentos;
- integridad de los datos.

Estas decisiones se definirán cuando se diseñe la siguiente versión.

## Regla

El agente NO debe implementar ninguna parte del sistema de sincronización durante Beta 1.