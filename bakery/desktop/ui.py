"""API pública del desktop UI (reexportaciones).

Los módulos concretos viven en archivos separados; este módulo conserva
los imports históricos (`from bakery.desktop.ui import ...`).
"""

from bakery.desktop.dialogs import (
    AddObservacionDialog,
    ConfirmSaleDialog,
    ProductFormDialog,
    SaleSavedDialog,
    SelectPaymentMethodDialog,
)
from bakery.desktop.historial_page import HistorialPage
from bakery.desktop.main_window import MainWindow
from bakery.desktop.menu_page import MenuPage
from bakery.desktop.products_page import ProductsPage
from bakery.desktop.register_sale_page import RegisterSalePage

__all__ = [
    "AddObservacionDialog",
    "ConfirmSaleDialog",
    "HistorialPage",
    "MainWindow",
    "MenuPage",
    "ProductFormDialog",
    "ProductsPage",
    "RegisterSalePage",
    "SaleSavedDialog",
    "SelectPaymentMethodDialog",
]
