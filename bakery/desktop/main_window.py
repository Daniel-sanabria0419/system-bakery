"""Ventana principal y navegación entre pantallas."""

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from bakery.desktop.client import ApiClient
from bakery.desktop.menu_page import MenuPage
from bakery.desktop.products_page import ProductsPage
from bakery.desktop.register_sale_page import RegisterSalePage

class MainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.setWindowTitle("Panadería")
        self.showFullScreen()
        self._api = api_client

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._menu = MenuPage(self.open_register_sale, self.open_products)
        self._register = RegisterSalePage(api_client, on_back=self.go_back_to_menu)
        self._products = ProductsPage(api_client, on_back=self.go_back_to_menu)
        self._stack.addWidget(self._menu)
        self._stack.addWidget(self._register)
        self._stack.addWidget(self._products)
        self._stack.setCurrentWidget(self._menu)

    def open_register_sale(self) -> None:
        self._register.load_payment_methods()
        self._register.load_catalog()
        self._stack.setCurrentWidget(self._register)

    def open_products(self) -> None:
        self._products.reload()
        self._stack.setCurrentWidget(self._products)

    def go_back_to_menu(self) -> None:
        self._stack.setCurrentWidget(self._menu)

