"""Migraciones SQLite ordenadas por schema_version.

Cada migración es idempotente respecto al estado físico de la DB.
No usar ORM ni framework externo.
"""

from __future__ import annotations

import sqlite3
from typing import Callable, List, Tuple

from bakery.persistence.schema import (
    create_schema_version_table,
    migrate_productos_ruta_imagen,
)

# Versión objetivo tras aplicar todas las migraciones listadas abajo.
CURRENT_SCHEMA_VERSION = 1

MigrationFn = Callable[[sqlite3.Connection], None]


def get_schema_version(connection: sqlite3.Connection) -> int:
    """Lee la versión aplicada. 0 si la meta no existe o no hay fila."""
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "schema_version" not in tables:
        return 0
    row = connection.execute(
        "SELECT version FROM schema_version WHERE id = 1"
    ).fetchone()
    if row is None:
        return 0
    return int(row[0])


def set_schema_version(connection: sqlite3.Connection, version: int) -> None:
    create_schema_version_table(connection)
    connection.execute(
        """
        INSERT INTO schema_version (id, version) VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET version = excluded.version
        """,
        (version,),
    )


def _migrate_to_v1(connection: sqlite3.Connection) -> None:
    """Baseline Beta 2.0.1: asegurar productos.ruta_imagen en bases ya creadas."""
    migrate_productos_ruta_imagen(connection)


# Lista ordenada: (versión destino, función). Se aplica si version actual < destino.
MIGRATIONS: List[Tuple[int, MigrationFn]] = [
    (1, _migrate_to_v1),
]


def apply_migrations(connection: sqlite3.Connection) -> int:
    """Aplica migraciones pendientes hasta CURRENT_SCHEMA_VERSION.

    Retorna la versión final. Idempotente.
    """
    create_schema_version_table(connection)
    version = get_schema_version(connection)
    for target, migrate in MIGRATIONS:
        if target > CURRENT_SCHEMA_VERSION:
            break
        if version < target:
            migrate(connection)
            set_schema_version(connection, target)
            version = target
    if version < CURRENT_SCHEMA_VERSION:
        set_schema_version(connection, CURRENT_SCHEMA_VERSION)
        version = CURRENT_SCHEMA_VERSION
    return version
