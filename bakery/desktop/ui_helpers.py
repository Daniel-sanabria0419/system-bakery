"""Helpers compartidos de layout/estilo para pantallas desktop."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from bakery.desktop import style

_PAYMENT_BUTTON_PLACEHOLDER = "Seleccionar medio de pago"
_PAYMENT_METHODS_PER_ROW = 5
_BACK_BUTTON_ARROW = "←"


def _apply_page_layout(layout: QVBoxLayout) -> None:
    layout.setContentsMargins(
        style.PAGE_MARGIN,
        style.PAGE_MARGIN,
        style.PAGE_MARGIN,
        style.PAGE_MARGIN,
    )
    layout.setSpacing(style.PAGE_SPACING)


def _apply_pad_button_size(button: QPushButton) -> None:
    if style.PAD_BUTTON_MIN_WIDTH > 0 or style.PAD_BUTTON_MIN_HEIGHT > 0:
        button.setMinimumSize(style.PAD_BUTTON_MIN_WIDTH, style.PAD_BUTTON_MIN_HEIGHT)


def _apply_dialog_action_button_size(button: QPushButton) -> None:
    if (
        style.DIALOG_ACTION_BUTTON_MIN_WIDTH > 0
        or style.DIALOG_ACTION_BUTTON_MIN_HEIGHT > 0
    ):
        button.setMinimumSize(
            style.DIALOG_ACTION_BUTTON_MIN_WIDTH,
            style.DIALOG_ACTION_BUTTON_MIN_HEIGHT,
        )


def _apply_touch_dialog_layout(dialog: QDialog, layout: QVBoxLayout) -> None:
    layout.setContentsMargins(
        style.DIALOG_CONTENT_MARGIN,
        style.DIALOG_CONTENT_MARGIN,
        style.DIALOG_CONTENT_MARGIN,
        style.DIALOG_CONTENT_MARGIN,
    )
    layout.setSpacing(style.DIALOG_CONTENT_SPACING)
    if style.DIALOG_MIN_WIDTH > 0 or style.DIALOG_MIN_HEIGHT > 0:
        dialog.setMinimumSize(style.DIALOG_MIN_WIDTH, style.DIALOG_MIN_HEIGHT)


def _apply_catalog_chip_icon(button: QToolButton, image_path: Optional[Path]) -> None:
    if image_path is None:
        button.setIcon(QIcon())
        return
    button.setIcon(QIcon(str(image_path)))
    button.setIconSize(QSize(36, 28))


def _make_separator(object_name: str) -> QFrame:
    line = QFrame()
    line.setObjectName(object_name)
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Plain)
    line.setFixedHeight(2)
    return line

