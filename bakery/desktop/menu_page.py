"""Página de menú principal."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QPushButton, QVBoxLayout, QWidget

from bakery.desktop import style

class MenuPage(QWidget):
    def __init__(self, on_register, on_products) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(
            style.MENU_MARGIN,
            style.MENU_MARGIN,
            style.MENU_MARGIN,
            style.MENU_MARGIN,
        )
        root.setSpacing(style.PAGE_SPACING)

        menu_grid = QWidget()
        menu_grid.setObjectName("menu_grid")
        grid = QGridLayout(menu_grid)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(style.PAGE_SPACING)

        register_button = QPushButton("Registrar venta")
        register_button.setObjectName("menu_register_button")
        style.apply_class(register_button, "menu-button")
        register_button.clicked.connect(on_register)
        grid.addWidget(register_button, 0, 0, Qt.AlignLeft | Qt.AlignTop)

        products_button = QPushButton("Productos")
        products_button.setObjectName("menu_products_button")
        style.apply_class(products_button, "menu-button")
        products_button.clicked.connect(on_products)
        grid.addWidget(products_button, 0, 1, Qt.AlignLeft | Qt.AlignTop)

        grid.setColumnStretch(2, 1)
        grid.setRowStretch(1, 1)

        root.addWidget(menu_grid, stretch=1)

