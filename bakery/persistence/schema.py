import sqlite3
from pathlib import Path
from typing import Optional

ESTADO_ACTIVO = 1
ESTADO_INACTIVO = 0

SEED_MEDIOS_PAGO = (
    "Efectivo",
    "Daviplata",
    "Nequi",
    "Bre-b",
    "Fiado",
)

# Semilla histórica Beta 2.0 (tabla vacía). «Pan pequeño» se garantiza aparte con ensure.
SEED_CATEGORIAS = (
    "Panadería",
    "Pastelería",
    "Bebidas",
    "Snacks",
    "Otros",
)

NOMBRE_CATEGORIA_PAN_PEQUENO = "Pan pequeño"

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
    id_estado INTEGER NOT NULL,
    ruta_imagen TEXT
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

_CREATE_SCHEMA_VERSION = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL CHECK (version >= 0)
)
"""


def create_schema_version_table(connection: sqlite3.Connection) -> None:
    connection.execute(_CREATE_SCHEMA_VERSION)


def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(_CREATE_MEDIOS_PAGO)
    connection.execute(_CREATE_VENTAS)
    connection.execute(_CREATE_CATEGORIAS)
    connection.execute(_CREATE_PRODUCTOS)
    connection.execute(_CREATE_VENTA_LINEAS)
    create_schema_version_table(connection)


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


def ensure_categoria(
    connection: sqlite3.Connection, nombre: str
) -> int:
    """Inserta la categoría por nombre exacto si falta. No borra existentes."""
    row = connection.execute(
        "SELECT id_categoria FROM categorias WHERE nombre = ?",
        (nombre,),
    ).fetchone()
    if row is not None:
        return int(row[0])
    cursor = connection.execute(
        "INSERT INTO categorias (nombre) VALUES (?)",
        (nombre,),
    )
    return int(cursor.lastrowid)


def ensure_categoria_pan_pequeno(connection: sqlite3.Connection) -> int:
    return ensure_categoria(connection, NOMBRE_CATEGORIA_PAN_PEQUENO)


def _productos_has_column(connection: sqlite3.Connection, column: str) -> bool:
    rows = connection.execute("PRAGMA table_info(productos)").fetchall()
    names = {row[1] for row in rows}
    return column in names


def migrate_productos_ruta_imagen(connection: sqlite3.Connection) -> None:
    """Añade productos.ruta_imagen si la tabla existe sin esa columna."""
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "productos" not in tables:
        return
    if _productos_has_column(connection, "ruta_imagen"):
        return
    connection.execute("ALTER TABLE productos ADD COLUMN ruta_imagen TEXT")


def ensure_imagenes_dirs(project_root: Optional[Path] = None) -> None:
    """Crea imagenes/categorias y imagenes/productos si faltan (idempotente)."""
    root = project_root
    if root is None:
        root = Path(__file__).resolve().parents[2]
    for relative in ("imagenes/categorias", "imagenes/productos"):
        (root / relative).mkdir(parents=True, exist_ok=True)
