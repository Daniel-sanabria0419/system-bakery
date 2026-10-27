"""Etapa 6 / scope §23: carpetas, asociar imagen, chips sin crash si falta."""

from pathlib import Path

from fastapi.testclient import TestClient
from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolButton

from bakery.api.app import create_app
from bakery.app.product_images import (
    category_image_path,
    ensure_imagenes_dirs,
    imagenes_categorias_dir,
    imagenes_productos_dir,
    normalize_ruta_imagen,
    project_root,
    resolve_relative_image,
    save_product_image,
)
from bakery.app.products import create_product, update_product
from bakery.desktop.main import create_window
from bakery.desktop.ui import ProductFormDialog
from bakery.persistence import initialize
from bakery.persistence.connection import connect
from tests.test_stage4_desktop import FakeApiClient, _click, _find

# PNG 1×1 mínimo válido
_PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _write_png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_PNG_1X1)
    return path


def test_imagenes_dirs_ready() -> None:
    ensure_imagenes_dirs()
    assert imagenes_categorias_dir().is_dir()
    assert imagenes_productos_dir().is_dir()
    root = project_root()
    assert (root / "imagenes" / "categorias").is_dir()
    assert (root / "imagenes" / "productos").is_dir()


def test_category_image_optional_by_convention(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "bakery.app.product_images.project_root", lambda: tmp_path
    )
    ensure_imagenes_dirs()
    assert category_image_path(1) is None
    _write_png(tmp_path / "imagenes" / "categorias" / "1.png")
    found = category_image_path(1)
    assert found is not None
    assert found.is_file()
    assert category_image_path(99) is None


def test_resolve_missing_image_returns_none(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "bakery.app.product_images.project_root", lambda: tmp_path
    )
    assert resolve_relative_image(None) is None
    assert resolve_relative_image("") is None
    assert resolve_relative_image("imagenes/productos/missing.png") is None
    assert resolve_relative_image("/etc/passwd") is None
    assert resolve_relative_image("../secret.png") is None


def test_save_and_normalize_product_image(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "bakery.app.product_images.project_root", lambda: tmp_path
    )
    source = _write_png(tmp_path / "origen.png")
    relative = save_product_image(7, source)
    assert relative == "imagenes/productos/7.png"
    assert (tmp_path / relative).is_file()
    assert normalize_ruta_imagen(relative) == relative
    assert normalize_ruta_imagen(None) is None


def test_create_associate_persist_edit_keeps_image(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "bakery.app.product_images.project_root", lambda: tmp_path
    )
    db_path = tmp_path / "bakery.sqlite3"
    initialize(db_path)
    source = _write_png(tmp_path / "foto.png")

    connection = connect(db_path)
    try:
        product = create_product(
            connection,
            nombre="Pan imagen",
            precio=3000,
            id_categoria=1,
        )
        assert product["ruta_imagen"] is None
        relative = save_product_image(product["id_producto"], source)
        updated = update_product(
            connection,
            product["id_producto"],
            nombre="Pan imagen",
            precio=3000,
            id_categoria=1,
            ruta_imagen=relative,
            actualizar_ruta_imagen=True,
        )
        assert updated["ruta_imagen"] == relative

        kept = update_product(
            connection,
            product["id_producto"],
            nombre="Pan imagen editado",
            precio=3500,
            id_categoria=1,
            actualizar_ruta_imagen=False,
        )
        assert kept["nombre"] == "Pan imagen editado"
        assert kept["ruta_imagen"] == relative
        assert resolve_relative_image(kept["ruta_imagen"]) is not None
    finally:
        connection.close()


def test_chips_without_image_do_not_crash(qtbot) -> None:
    api = FakeApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))

    category = _find(window, "sale_category_1")
    assert isinstance(category, QToolButton)
    # Sin archivo de categoría: placeholder / solo texto, sin crash
    assert category.text() != ""

    _click(qtbot, _find(window, "sale_category_todos"))
    product = _find(window, "sale_product_1")
    assert isinstance(product, QToolButton)
    assert product.icon().isNull() or isinstance(product.icon(), QIcon)


def test_api_ruta_imagen_create_and_edit_keeps(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "bakery.app.product_images.project_root", lambda: tmp_path
    )
    source = _write_png(tmp_path / "api.png")
    with TestClient(create_app(tmp_path / "bakery.sqlite3")) as client:
        created = client.post(
            "/productos",
            json={
                "nombre": "Con imagen",
                "precio": 2000,
                "id_categoria": 1,
            },
        )
        assert created.status_code == 200
        product = created.json()
        assert product["ruta_imagen"] is None

        relative = save_product_image(product["id_producto"], source)
        attached = client.put(
            f"/productos/{product['id_producto']}",
            json={
                "nombre": "Con imagen",
                "precio": 2000,
                "id_categoria": 1,
                "ruta_imagen": relative,
                "actualizar_ruta_imagen": True,
            },
        )
        assert attached.status_code == 200
        assert attached.json()["ruta_imagen"] == relative

        edited = client.put(
            f"/productos/{product['id_producto']}",
            json={
                "nombre": "Renombrado",
                "precio": 2500,
                "id_categoria": 1,
                "actualizar_ruta_imagen": False,
            },
        )
        assert edited.status_code == 200
        assert edited.json()["nombre"] == "Renombrado"
        assert edited.json()["ruta_imagen"] == relative


def test_product_form_has_image_controls(qtbot) -> None:
    dialog = ProductFormDialog(
        [{"id_categoria": 1, "nombre": "Panadería"}],
        product={
            "id_producto": 1,
            "nombre": "Pan",
            "precio": 1000,
            "id_categoria": 1,
            "descripcion": None,
            "id_estado": 1,
            "ruta_imagen": "imagenes/productos/1.png",
        },
    )
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.findChild(QObject, "product_image_button") is not None
    status = dialog.findChild(QObject, "product_image_status")
    assert status is not None
    assert "imagenes/productos/1.png" in status.text()
    assert dialog.image_changed() is False
    assert dialog.pending_image_path() is None


def test_product_chip_shows_icon_when_file_exists(
    qtbot, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "bakery.app.product_images.project_root", lambda: tmp_path
    )
    ensure_imagenes_dirs()
    relative = "imagenes/productos/1.png"
    _write_png(tmp_path / relative)

    api = FakeApiClient(
        products=[
            {
                "id_producto": 1,
                "nombre": "Pan",
                "precio": 5000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": 1,
                "ruta_imagen": relative,
            },
            {
                "id_producto": 2,
                "nombre": "Sin foto",
                "precio": 3000,
                "id_categoria": 1,
                "descripcion": None,
                "id_estado": 1,
                "ruta_imagen": None,
            },
        ]
    )
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_register_button"))
    _click(qtbot, _find(window, "sale_category_todos"))

    with_image = _find(window, "sale_product_1")
    without = _find(window, "sale_product_2")
    assert isinstance(with_image, QToolButton)
    assert isinstance(without, QToolButton)
    assert not with_image.icon().isNull()
    assert without.icon().isNull()
