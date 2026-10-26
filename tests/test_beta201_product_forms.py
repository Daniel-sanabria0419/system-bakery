"""Etapa 7 / scope §15 y §22: Crear y Editar producto con el mismo estilo."""

from PySide6.QtCore import QObject
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit

from bakery.desktop import style
from bakery.desktop.main import create_window
from bakery.desktop.ui import ProductFormDialog
from bakery.persistence.schema import ESTADO_ACTIVO
from tests.test_beta2_desktop_products import FakeProductsApiClient, _click, _find


def _categories() -> list:
    return [
        {"id_categoria": 1, "nombre": "Panadería"},
        {"id_categoria": 2, "nombre": "Bebidas"},
    ]


def _assert_form_field_style(widget) -> None:
    assert widget.property("class") == style.PRODUCT_FORM_FIELD_CLASS


def _hex_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    r = int(value[0:2], 16) / 255.0
    g = int(value[2:4], 16) / 255.0
    b = int(value[4:6], 16) / 255.0
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def test_style_constants_placeholder_darker_than_app_bg() -> None:
    assert style.APP_BACKGROUND == "#F5F0E8"
    assert style.PRODUCT_FORM_FIELD_TEXT == "#000000"
    assert style.PRODUCT_FORM_PLACEHOLDER == "#5C5346"
    assert _hex_luminance(style.PRODUCT_FORM_PLACEHOLDER) < _hex_luminance(
        style.APP_BACKGROUND
    )
    qss = style.load_theme_qss()
    assert 'QLineEdit[class="product-form-field"]' in qss
    assert 'QComboBox[class="product-form-field"]' in qss
    assert style.PRODUCT_FORM_PLACEHOLDER in qss
    assert style.PRODUCT_FORM_FIELD_TEXT in qss
    assert "placeholder-text-color" in qss


def test_create_and_edit_share_field_classes(qtbot) -> None:
    create = ProductFormDialog(_categories())
    qtbot.addWidget(create)
    create.show()

    edit = ProductFormDialog(
        _categories(),
        product={
            "id_producto": 1,
            "nombre": "Pan",
            "precio": 3000,
            "id_categoria": 1,
            "descripcion": "x",
            "id_estado": ESTADO_ACTIVO,
            "ruta_imagen": None,
        },
    )
    qtbot.addWidget(edit)
    edit.show()

    for dialog in (create, edit):
        assert dialog.objectName() == "product_form_dialog"
        nombre = dialog.findChild(QLineEdit, "product_nombre_input")
        precio = dialog.findChild(QLineEdit, "product_precio_input")
        descripcion = dialog.findChild(QLineEdit, "product_descripcion_input")
        combo = dialog.findChild(QComboBox, "product_categoria_combo")
        assert nombre is not None and precio is not None and descripcion is not None
        assert combo is not None
        for field in (nombre, precio, descripcion, combo):
            _assert_form_field_style(field)
        assert dialog.findChild(
            QObject, "product_image_status"
        ).property("class") == style.PRODUCT_FORM_LABEL_CLASS
        assert dialog.findChild(
            QObject, "product_estado_label"
        ).property("class") == style.PRODUCT_FORM_LABEL_CLASS
        assert dialog.findChild(
            QObject, "product_image_button"
        ).property("class") == "product-form-button"


def test_typed_text_is_black_and_placeholder_role_set(qtbot) -> None:
    app = QApplication.instance()
    assert app is not None
    app.setStyleSheet(style.load_theme_qss())

    dialog = ProductFormDialog(_categories())
    qtbot.addWidget(dialog)
    dialog.show()
    QApplication.processEvents()

    nombre = dialog.findChild(QLineEdit, "product_nombre_input")
    assert nombre is not None
    nombre.setText("Pan de queso")
    text_color = nombre.palette().color(QPalette.ColorRole.Text)
    # Con QSS color:#000000 el texto debe ser negro (o casi).
    assert text_color.lightness() <= 40 or text_color == QColor(
        style.PRODUCT_FORM_FIELD_TEXT
    )

    placeholder = nombre.palette().color(QPalette.ColorRole.PlaceholderText)
    # Si el estilo aplica placeholder-text-color, debe ser más oscuro que el fondo.
    if placeholder.isValid() and placeholder.alpha() > 0:
        bg = QColor(style.APP_BACKGROUND)
        assert placeholder.lightness() < bg.lightness()


def test_create_edit_still_save_after_style(qtbot) -> None:
    api = FakeProductsApiClient()
    window = create_window(api)
    qtbot.addWidget(window)
    window.show()
    _click(qtbot, _find(window, "menu_products_button"))

    from tests.test_beta2_desktop_products import _fill_and_save_product_dialog

    _fill_and_save_product_dialog(nombre="Galleta", precio="1500", id_categoria=1)
    _click(qtbot, _find(window, "new_product_button"))
    qtbot.waitUntil(lambda: len(api.products) == 1, timeout=2000)
    assert api.products[0]["nombre"] == "Galleta"

    _fill_and_save_product_dialog(nombre="Galleta 2", precio="1800", id_categoria=2)
    _click(qtbot, _find(window, "edit_product_1"))
    qtbot.waitUntil(
        lambda: api.products and api.products[0]["nombre"] == "Galleta 2",
        timeout=2000,
    )
    assert api.products[0]["precio"] == 1800
