import sqlite3

ESTADO_ACTIVO = 1
ESTADO_INACTIVO = 0

SEED_MEDIOS_PAGO = (
    "Efectivo",
    "Daviplata",
    "Nequi",
    "Bre-b",
    "Fiado",
)

SEED_CATEGORIAS = (
    "Panadería",
    "Pastelería",
    "Bebidas",
    "Snacks",
    "Otros",
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

_CREATE_CATEGORIAS = """
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL
)
"""

_CREATE_PRODUCTOS = """
CREATE TABLE IF NOT EXISTS productos (
    id_producto INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio INTEGER NOT NULL CHECK (precio > 0),
    id_categoria INTEGER NOT NULL REFERENCES categorias(id_categoria),
    descripcion TEXT,
    id_estado INTEGER NOT NULL
)
"""

_CREATE_VENTA_LINEAS = """
CREATE TABLE IF NOT EXISTS venta_lineas (
    id_linea INTEGER PRIMARY KEY,
    id_venta TEXT NOT NULL REFERENCES ventas(id_venta),
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
    nombre_producto TEXT NOT NULL,
    precio_aplicado INTEGER NOT NULL CHECK (precio_aplicado > 0),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    subtotal INTEGER NOT NULL CHECK (subtotal > 0)
)
"""


def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(_CREATE_MEDIOS_PAGO)
    connection.execute(_CREATE_VENTAS)
    connection.execute(_CREATE_CATEGORIAS)
    connection.execute(_CREATE_PRODUCTOS)
    connection.execute(_CREATE_VENTA_LINEAS)


def seed_payment_methods(connection: sqlite3.Connection) -> None:
    count = connection.execute("SELECT COUNT(*) FROM medios_pago").fetchone()[0]
    if count:
        return
    connection.executemany(
        "INSERT INTO medios_pago (nombre, id_estado) VALUES (?, ?)",
        [(nombre, ESTADO_ACTIVO) for nombre in SEED_MEDIOS_PAGO],
    )


def seed_categorias(connection: sqlite3.Connection) -> None:
    count = connection.execute("SELECT COUNT(*) FROM categorias").fetchone()[0]
    if count:
        return
    connection.executemany(
        "INSERT INTO categorias (nombre) VALUES (?)",
        [(nombre,) for nombre in SEED_CATEGORIAS],
    )
