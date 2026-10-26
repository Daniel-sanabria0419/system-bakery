"""Rutas y copia de imágenes de catálogo (categorías por convención, productos en DB)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional, Sequence

_IMAGE_EXTENSIONS: Sequence[str] = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def imagenes_categorias_dir() -> Path:
    return project_root() / "imagenes" / "categorias"


def imagenes_productos_dir() -> Path:
    return project_root() / "imagenes" / "productos"


def ensure_imagenes_dirs() -> None:
    imagenes_categorias_dir().mkdir(parents=True, exist_ok=True)
    imagenes_productos_dir().mkdir(parents=True, exist_ok=True)


def resolve_relative_image(ruta: Optional[str]) -> Optional[Path]:
    """Devuelve Path absoluto si el archivo relativo existe; si no, None."""
    if not isinstance(ruta, str) or not ruta.strip():
        return None
    relative = ruta.strip().replace("\\", "/")
    if relative.startswith("/") or ".." in relative.split("/"):
        return None
    path = project_root() / relative
    return path if path.is_file() else None


def category_image_path(id_categoria: int) -> Optional[Path]:
    """Convención: imagenes/categorias/{id}.{ext}. None si no hay archivo."""
    if isinstance(id_categoria, bool) or not isinstance(id_categoria, int):
        return None
    base = imagenes_categorias_dir()
    for ext in _IMAGE_EXTENSIONS:
        candidate = base / f"{id_categoria}{ext}"
        if candidate.is_file():
            return candidate
    return None


def save_product_image(id_producto: int, source: Path) -> str:
    """Copia la imagen a imagenes/productos/{id}{ext} y devuelve ruta relativa."""
    if isinstance(id_producto, bool) or not isinstance(id_producto, int) or id_producto <= 0:
        raise ValueError("id_producto inválido.")
    source_path = Path(source)
    if not source_path.is_file():
        raise ValueError("El archivo de imagen no existe.")
    ext = source_path.suffix.lower()
    if ext not in _IMAGE_EXTENSIONS:
        raise ValueError("Formato de imagen no soportado.")
    ensure_imagenes_dirs()
    dest_dir = imagenes_productos_dir()
    for old in dest_dir.glob(f"{id_producto}.*"):
        if old.is_file():
            old.unlink()
    dest = dest_dir / f"{id_producto}{ext}"
    shutil.copy2(source_path, dest)
    return f"imagenes/productos/{id_producto}{ext}"


def normalize_ruta_imagen(ruta: Optional[str]) -> Optional[str]:
    if ruta is None:
        return None
    if not isinstance(ruta, str):
        raise ValueError("La ruta de imagen debe ser texto.")
    normalized = ruta.strip().replace("\\", "/")
    if not normalized:
        return None
    if normalized.startswith("/") or ".." in normalized.split("/"):
        raise ValueError("Ruta de imagen inválida.")
    if not normalized.startswith("imagenes/productos/"):
        raise ValueError("La imagen de producto debe estar en imagenes/productos/.")
    return normalized
