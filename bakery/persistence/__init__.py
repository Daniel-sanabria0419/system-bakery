from pathlib import Path

from bakery.persistence.connection import DEFAULT_DB_PATH, connect
from bakery.persistence.schema import (
    create_schema,
    ensure_categoria_pan_pequeno,
    ensure_imagenes_dirs,
    migrate_productos_ruta_imagen,
    seed_categorias,
    seed_payment_methods,
)


def initialize(db_path: Path = DEFAULT_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(db_path)
    try:
        create_schema(connection)
        migrate_productos_ruta_imagen(connection)
        seed_payment_methods(connection)
        seed_categorias(connection)
        ensure_categoria_pan_pequeno(connection)
        connection.commit()
    finally:
        connection.close()
    ensure_imagenes_dirs()
