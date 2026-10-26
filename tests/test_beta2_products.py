from pathlib import Path

import pytest

from bakery.app.products import (
    ProductValidationError,
    activate_product,
    create_product,
    deactivate_product,
    find_active_products_by_price,
    get_product,
    list_active_products,
    list_all_products,
    list_categories,
    update_product,
)
from bakery.persistence import initialize
from bakery.persistence.connection import connect
from bakery.persistence.repositories import (
    get_producto,
    insert_producto,
    list_active_productos,
    list_categorias,
)
from bakery.persistence.schema import (
    ESTADO_ACTIVO,
    ESTADO_INACTIVO,
    NOMBRE_CATEGORIA_PAN_PEQUENO,
    SEED_CATEGORIAS,
)


def _db(tmp_path: Path) -> Path:
    path = tmp_path / "bakery.sqlite3"
    initialize(path)
    return path


def test_list_categorias_returns_seed(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        categories = list_categorias(connection)
        assert [c["nombre"] for c in categories] == list(SEED_CATEGORIAS) + [
            NOMBRE_CATEGORIA_PAN_PEQUENO
        ]
        assert list_categories(connection) == categories
    finally:
        connection.close()


def test_persistence_insert_and_list_active_by_filters(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        id_a = insert_producto(
            connection,
            nombre="Pan",
            precio=2500,
            id_categoria=1,
            descripcion=None,
            id_estado=ESTADO_ACTIVO,
        )
        insert_producto(
            connection,
            nombre="Torta",
            precio=2500,
            id_categoria=2,
            descripcion="grande",
            id_estado=ESTADO_ACTIVO,
        )
        id_inactive = insert_producto(
            connection,
            nombre="Viejo",
            precio=2500,
            id_categoria=1,
            descripcion=None,
            id_estado=ESTADO_INACTIVO,
        )
        connection.commit()

        by_price = list_active_productos(connection, precio=2500)
        assert [p["id_producto"] for p in by_price] == [id_a, id_a + 1]
        assert all(p["id_producto"] != id_inactive for p in by_price)

        by_cat = list_active_productos(connection, id_categoria=1)
        assert [p["nombre"] for p in by_cat] == ["Pan"]
    finally:
        connection.close()


def test_create_product_defaults_active(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        product = create_product(
            connection,
            nombre="  Pan de queso  ",
            precio=3000,
            id_categoria=1,
            descripcion="  fresco  ",
        )
        assert product["nombre"] == "Pan de queso"
        assert product["precio"] == 3000
        assert product["id_categoria"] == 1
        assert product["descripcion"] == "fresco"
        assert product["id_estado"] == ESTADO_ACTIVO
        assert get_product(connection, product["id_producto"]) == product
    finally:
        connection.close()


def test_create_product_rejects_invalid_price_and_category(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        with pytest.raises(ProductValidationError, match="precio"):
            create_product(connection, nombre="Pan", precio=0, id_categoria=1)
        with pytest.raises(ProductValidationError, match="precio"):
            create_product(connection, nombre="Pan", precio=2500.5, id_categoria=1)  # type: ignore[arg-type]
        with pytest.raises(ProductValidationError, match="categoría"):
            create_product(connection, nombre="Pan", precio=1000, id_categoria=999)
        with pytest.raises(ProductValidationError, match="nombre"):
            create_product(connection, nombre="   ", precio=1000, id_categoria=1)
    finally:
        connection.close()


def test_update_product_changes_fields_keeps_estado(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        product = create_product(
            connection, nombre="Pan", precio=2000, id_categoria=1
        )
        updated = update_product(
            connection,
            product["id_producto"],
            nombre="Pan integral",
            precio=2500,
            id_categoria=2,
            descripcion="nuevo",
        )
        assert updated["nombre"] == "Pan integral"
        assert updated["precio"] == 2500
        assert updated["id_categoria"] == 2
        assert updated["descripcion"] == "nuevo"
        assert updated["id_estado"] == ESTADO_ACTIVO
    finally:
        connection.close()


def test_deactivate_excludes_from_active_search(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        product = create_product(
            connection, nombre="Café", precio=4000, id_categoria=3
        )
        create_product(connection, nombre="Café 2", precio=4000, id_categoria=3)
        deactivate_product(connection, product["id_producto"])

        active = list_active_products(connection)
        assert [p["nombre"] for p in active] == ["Café 2"]

        by_price = find_active_products_by_price(connection, 4000)
        assert [p["nombre"] for p in by_price] == ["Café 2"]

        by_cat = list_active_products(connection, id_categoria=3)
        assert [p["nombre"] for p in by_cat] == ["Café 2"]

        all_products = list_all_products(connection)
        assert len(all_products) == 2
        stored = get_producto(connection, product["id_producto"])
        assert stored is not None
        assert stored["id_estado"] == ESTADO_INACTIVO
    finally:
        connection.close()


def test_activate_product_restores_listings(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        product = create_product(
            connection, nombre="Galleta", precio=1500, id_categoria=4
        )
        deactivate_product(connection, product["id_producto"])
        restored = activate_product(connection, product["id_producto"])
        assert restored["id_estado"] == ESTADO_ACTIVO
        assert find_active_products_by_price(connection, 1500) == [restored]
    finally:
        connection.close()


def test_deactivate_keeps_row_no_delete_api(tmp_path: Path) -> None:
    import bakery.app.products as products_module

    connection = connect(_db(tmp_path))
    try:
        product = create_product(
            connection, nombre="Empanada", precio=2000, id_categoria=1
        )
        deactivate_product(connection, product["id_producto"])
        assert get_producto(connection, product["id_producto"]) is not None
        assert not hasattr(products_module, "delete_product")
    finally:
        connection.close()


def test_update_missing_product_raises(tmp_path: Path) -> None:
    connection = connect(_db(tmp_path))
    try:
        with pytest.raises(ProductValidationError, match="no existe"):
            update_product(
                connection,
                999,
                nombre="X",
                precio=1000,
                id_categoria=1,
            )
    finally:
        connection.close()
