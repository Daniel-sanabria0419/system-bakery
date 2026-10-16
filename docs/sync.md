# Synchronization

## Estado

La sincronización con la base de datos en la nube está FUERA DEL ALCANCE.

## Beta 1 y Beta 1.1

Las ventas se almacenan únicamente en SQLite local.

**Beta 1.1 no introduce ni modifica ningún comportamiento de sincronización.**

Los cambios de Beta 1.1 (lista de compra en memoria, calculadora local, navegación, popup de éxito) afectan solo al flujo de registro en desktop y a la lógica local. El `POST /ventas` sigue persistiendo un único `valor_total` en SQLite.

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

Estas decisiones se definirán cuando se diseñe esa versión.

## Regla

El agente NO debe implementar ninguna parte del sistema de sincronización durante Beta 1 ni Beta 1.1.
