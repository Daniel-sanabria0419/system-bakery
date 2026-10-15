import sqlite3

ESTADO_ACTIVO = 1

SEED_MEDIOS_PAGO = (
    "Efectivo",
    "Daviplata",
    "Nequi",
    "Bre-b",
    "Fiado",
)

_CREATE_MEDIOS_PAGO = """
CREATE TABLE IF NOT EXISTS medios_pago (
    id_medio_pago INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    id_estado INTEGER NOT NULL
)
"""

_CREATE_VENTAS = """
CREATE TABLE IF NOT EXISTS ventas (
    id_venta TEXT PRIMARY KEY,
    valor_total INTEGER NOT NULL CHECK (valor_total > 0),
    fecha_venta TEXT NOT NULL,
    id_medio_pago INTEGER NOT NULL REFERENCES medios_pago(id_medio_pago),
    caja INTEGER NOT NULL DEFAULT 1,
    tendero INTEGER NOT NULL DEFAULT 1
)
"""


def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(_CREATE_MEDIOS_PAGO)
    connection.execute(_CREATE_VENTAS)


def seed_payment_methods(connection: sqlite3.Connection) -> None:
    count = connection.execute("SELECT COUNT(*) FROM medios_pago").fetchone()[0]
    if count:
        return
    connection.executemany(
        "INSERT INTO medios_pago (nombre, id_estado) VALUES (?, ?)",
        [(nombre, ESTADO_ACTIVO) for nombre in SEED_MEDIOS_PAGO],
    )
