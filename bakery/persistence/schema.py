import json
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

# Semilla histórica Beta 2.0 (tabla vacía). «Pan pequeño» se garantiza aparte con ensure.
SEED_CATEGORIAS = (
    "Panadería",
    "Pastelería",
    "Bebidas",
    "Snacks",
    "Otros",
)

NOMBRE_CATEGORIA_PAN_PEQUENO = "Pan pequeño"

# Semilla Beta 2.0.4 Etapa 2 (cobro sigue por nombre de categoría hasta dual-path).
NOMBRE_PROMOCION_PAN_PEQUENO = "Pan pequeño 7 por 2000"
TIPO_PROMOCION_CANTIDAD_POR_MONTO = "cantidad_por_monto"
# JSON exacto en DB. El cobro lee precio_base y modo; los nudos están en el motor.
PROMOCION_PAN_PEQUENO_CONFIG = {
    "precio_base": 300,
    "modo": "ceil",
}

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

_CREATE_PROMOCIONES = """
CREATE TABLE IF NOT EXISTS promociones (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    configuracion TEXT NOT NULL,
    activo INTEGER NOT NULL
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
    ruta_imagen TEXT,
    promocion_id INTEGER REFERENCES promociones(id)
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
    subtotal INTEGER NOT NULL CHECK (subtotal > 0),
    total INTEGER NOT NULL CHECK (total > 0),
    id_promocion INTEGER REFERENCES promociones(id),
    nombre_promocion TEXT
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
    connection.execute(_CREATE_PROMOCIONES)
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


def promocion_pan_pequeno_config_json() -> str:
    """JSON canónico de la promo Pan pequeño (orden de claves estable)."""
    return json.dumps(PROMOCION_PAN_PEQUENO_CONFIG, separators=(",", ":"), sort_keys=True)


def ensure_promocion_pan_pequeno(connection: sqlite3.Connection) -> int:
    """Inserta o actualiza la promo canónica Pan pequeño. Idempotente."""
    config_json = promocion_pan_pequeno_config_json()
    row = connection.execute(
        "SELECT id FROM promociones WHERE nombre = ?",
        (NOMBRE_PROMOCION_PAN_PEQUENO,),
    ).fetchone()
    if row is not None:
        promo_id = int(row[0])
        connection.execute(
            """
            UPDATE promociones
            SET tipo = ?, configuracion = ?, activo = ?
            WHERE id = ?
            """,
            (
                TIPO_PROMOCION_CANTIDAD_POR_MONTO,
                config_json,
                ESTADO_ACTIVO,
                promo_id,
            ),
        )
        return promo_id
    cursor = connection.execute(
        """
        INSERT INTO promociones (nombre, tipo, configuracion, activo)
        VALUES (?, ?, ?, ?)
        """,
        (
            NOMBRE_PROMOCION_PAN_PEQUENO,
            TIPO_PROMOCION_CANTIDAD_POR_MONTO,
            config_json,
            ESTADO_ACTIVO,
        ),
    )
    return int(cursor.lastrowid)


def backfill_productos_promocion_pan_pequeno(
    connection: sqlite3.Connection,
) -> int:
    """Asigna promocion_id a todos los productos de categoría Pan pequeño.

    Retorna el id de la promo. Idempotente. No toca productos de otras categorías.
    """
    id_categoria = ensure_categoria_pan_pequeno(connection)
    promo_id = ensure_promocion_pan_pequeno(connection)
    connection.execute(
        """
        UPDATE productos
        SET promocion_id = ?
        WHERE id_categoria = ?
        """,
        (promo_id, id_categoria),
    )
    return promo_id


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


def ensure_promociones_table(connection: sqlite3.Connection) -> None:
    """Crea la tabla promociones si falta (idempotente)."""
    connection.execute(_CREATE_PROMOCIONES)


def migrate_productos_promocion_id(connection: sqlite3.Connection) -> None:
    """Añade productos.promocion_id nullable FK si la tabla existe sin esa columna."""
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "productos" not in tables:
        return
    if _productos_has_column(connection, "promocion_id"):
        return
    connection.execute(
        "ALTER TABLE productos ADD COLUMN promocion_id INTEGER "
        "REFERENCES promociones(id)"
    )


def _venta_lineas_has_column(connection: sqlite3.Connection, column: str) -> bool:
    rows = connection.execute("PRAGMA table_info(venta_lineas)").fetchall()
    names = {row[1] for row in rows}
    return column in names


def migrate_venta_lineas_total(connection: sqlite3.Connection) -> None:
    """Añade venta_lineas.total y copia el subtotal ya guardado.

    No recalcula el subtotal viejo: ese número sigue siendo el monto que
    se cobró entonces. Las ventas nuevas calculan subtotal y total aparte.
    """
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "venta_lineas" not in tables:
        return
    if _venta_lineas_has_column(connection, "total"):
        return
    if not _venta_lineas_has_column(connection, "id_promocion"):
        raise RuntimeError(
            "venta_lineas.total requiere el snapshot de promo (schema v3)."
        )
    ddl = _CREATE_VENTA_LINEAS.replace(
        "CREATE TABLE IF NOT EXISTS venta_lineas",
        "CREATE TABLE venta_lineas_new",
    )
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        connection.executescript(
            f"""
            DROP TABLE IF EXISTS venta_lineas_new;
            {ddl};
            INSERT INTO venta_lineas_new (
                id_linea, id_venta, id_producto, nombre_producto,
                precio_aplicado, cantidad, subtotal, total,
                id_promocion, nombre_promocion
            )
            SELECT
                id_linea, id_venta, id_producto, nombre_producto,
                precio_aplicado, cantidad, subtotal, subtotal,
                id_promocion, nombre_promocion
            FROM venta_lineas;
            DROP TABLE venta_lineas;
            ALTER TABLE venta_lineas_new RENAME TO venta_lineas;
            """
        )
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def migrate_venta_lineas_promocion_snapshot(
    connection: sqlite3.Connection,
) -> None:
    """Añade id_promocion / nombre_promocion en venta_lineas si faltan."""
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "venta_lineas" not in tables:
        return
    if not _venta_lineas_has_column(connection, "id_promocion"):
        connection.execute(
            "ALTER TABLE venta_lineas ADD COLUMN id_promocion INTEGER "
            "REFERENCES promociones(id)"
        )
    if not _venta_lineas_has_column(connection, "nombre_promocion"):
        connection.execute(
            "ALTER TABLE venta_lineas ADD COLUMN nombre_promocion TEXT"
        )


def migrate_promociones_config_slim(connection: sqlite3.Connection) -> None:
    """Backfill: ``configuracion`` canónica solo ``precio_base`` + ``modo``."""
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "promociones" not in tables:
        return
    config_json = promocion_pan_pequeno_config_json()
    connection.execute(
        """
        UPDATE promociones
        SET configuracion = ?, tipo = ?, activo = ?
        WHERE nombre = ?
        """,
        (
            config_json,
            TIPO_PROMOCION_CANTIDAD_POR_MONTO,
            ESTADO_ACTIVO,
            NOMBRE_PROMOCION_PAN_PEQUENO,
        ),
    )
