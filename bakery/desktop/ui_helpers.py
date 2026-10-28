"""Helpers compartidos de layout/estilo para pantallas desktop."""

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QTextOption
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QLayout,
    QLayoutItem,
    QPushButton,
    QStyle,
    QStyleOptionToolButton,
    QStylePainter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from bakery.app.product_images import PRODUCT_THUMB_MAX_EDGE, product_thumb_path
from bakery.desktop import style

_PAYMENT_BUTTON_PLACEHOLDER = "Seleccionar medio de pago"
_PAYMENT_METHODS_PER_ROW = 5
_BACK_BUTTON_ARROW = "←"
_CHIP_ICON_SIZE = QSize(60, 60)
_CHIP_ICON_CACHE: Dict[str, QIcon] = {}


def _apply_page_layout(layout: QVBoxLayout) -> None:
    layout.setContentsMargins(
        style.PAGE_MARGIN,
        style.PAGE_MARGIN,
        style.PAGE_MARGIN,
        style.PAGE_MARGIN,
    )
    layout.setSpacing(style.PAGE_SPACING)


def _apply_action_button_size(button: QPushButton) -> None:
    """Tamaño mínimo táctil para Medio / Borrar todo / Pagar (Beta 2.0.6)."""
    if style.ACTION_BUTTON_MIN_WIDTH > 0 or style.ACTION_BUTTON_MIN_HEIGHT > 0:
        button.setMinimumSize(
            style.ACTION_BUTTON_MIN_WIDTH,
            style.ACTION_BUTTON_MIN_HEIGHT,
        )


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


def clear_chip_icon_cache(path: Optional[Path] = None) -> None:
    """Invalida caché de iconos (toda o una ruta concreta + su thumb)."""
    if path is None:
        _CHIP_ICON_CACHE.clear()
        return
    keys = {str(path), str(product_thumb_path(path))}
    for key in keys:
        _CHIP_ICON_CACHE.pop(key, None)


def ensure_product_thumbnail(
    full_image: Path, *, max_edge: int = PRODUCT_THUMB_MAX_EDGE
) -> Path:
    """Crea/actualiza `{stem}_thumb{ext}` con QImage. Fallback: imagen completa."""
    full_path = Path(full_image)
    if not full_path.is_file():
        return full_path
    thumb = product_thumb_path(full_path)
    try:
        if thumb.is_file() and thumb.stat().st_mtime >= full_path.stat().st_mtime:
            return thumb
    except OSError:
        pass
    image = QImage(str(full_path))
    if image.isNull():
        return full_path
    scaled = image.scaled(
        max_edge,
        max_edge,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )
    if not scaled.save(str(thumb)):
        return full_path
    clear_chip_icon_cache(full_path)
    return thumb if thumb.is_file() else full_path


def _apply_catalog_chip_icon(
    button: QToolButton,
    image_path: Optional[Path],
    *,
    ensure_thumb: bool = False,
) -> None:
    if image_path is None:
        button.setIcon(QIcon())
        button.setIconSize(_CHIP_ICON_SIZE)
        return
    path = Path(image_path)
    if ensure_thumb:
        path = ensure_product_thumbnail(path)
    key = str(path)
    icon = _CHIP_ICON_CACHE.get(key)
    if icon is None:
        icon = QIcon(key)
        _CHIP_ICON_CACHE[key] = icon
    button.setIcon(icon)
    button.setIconSize(_CHIP_ICON_SIZE)


class CatalogChipButton(QToolButton):
    """Chip de catálogo: el nombre parte de renglón en vez de cortarse con ..."""

    def paintEvent(self, event) -> None:
        painter = QStylePainter(self)
        option = QStyleOptionToolButton()
        self.initStyleOption(option)
        label = option.text
        icon = QIcon(option.icon)
        option.text = ""
        option.icon = QIcon()
        painter.drawComplexControl(QStyle.CC_ToolButton, option)

        pad = style.PRODUCT_CHIP_IMAGE_PADDING
        contents = self.rect().adjusted(pad, pad, -pad, -pad)
        icon_size = self.iconSize()
        has_icon = (
            not icon.isNull()
            and icon_size.width() > 0
            and icon_size.height() > 0
        )
        if has_icon:
            icon_rect = QRect(
                contents.x() + max(0, (contents.width() - icon_size.width()) // 2),
                contents.y(),
                min(icon_size.width(), contents.width()),
                min(icon_size.height(), contents.height()),
            )
            icon.paint(painter, icon_rect, Qt.AlignCenter)
            text_top = icon_rect.bottom() + 1 + pad
            text_rect = QRect(
                contents.x(),
                text_top,
                contents.width(),
                max(0, contents.bottom() - text_top + 1),
            )
            alignment = Qt.AlignHCenter | Qt.AlignTop
        else:
            text_rect = QRect(contents)
            alignment = Qt.AlignCenter
        if not label or text_rect.height() <= 0:
            return
        painter.setFont(option.font)
        painter.setPen(option.palette.color(option.palette.ColorRole.ButtonText))
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        text_option.setAlignment(alignment)
        painter.drawText(QRectF(text_rect), label, text_option)


def _make_separator(object_name: str) -> QFrame:
    line = QFrame()
    line.setObjectName(object_name)
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Plain)
    line.setFixedHeight(2)
    return line


def catalog_chips_per_row(
    available_width: int,
    chip_width: int,
    spacing: int = style.PAGE_SPACING,
) -> int:
    """Cuántos chips caben en una fila según el ancho (mínimo 1)."""
    if available_width <= 0 or chip_width <= 0:
        return 1
    return max(1, (available_width + spacing) // (chip_width + spacing))


class FlowLayout(QLayout):
    """Filas wrap según ancho disponible; sin columnas fijas."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        h_spacing: int = style.PAGE_SPACING,
        v_spacing: int = style.PAGE_SPACING,
    ) -> None:
        super().__init__(parent)
        self._items: List[QLayoutItem] = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(
            margins.left() + margins.right(),
            margins.top() + margins.bottom(),
        )
        return size

    def _do_layout(self, rect: QRect, *, test_only: bool) -> int:
        margins = self.contentsMargins()
        effective = rect.adjusted(
            margins.left(),
            margins.top(),
            -margins.right(),
            -margins.bottom(),
        )
        x = effective.x()
        y = effective.y()
        line_height = 0
        space_x = self._h_spacing
        space_y = self._v_spacing

        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width() + space_x
            if next_x - space_x > effective.right() and line_height > 0:
                x = effective.x()
                y = y + line_height + space_y
                next_x = x + hint.width() + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y() + margins.bottom()
