from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from bakery.app.products import (
    ProductValidationError,
    activate_product,
    create_product,
    deactivate_product,
    get_product,
    list_active_products,
    list_all_products,
    list_categories,
    update_product,
)
from bakery.app.sales import SaleValidationError, register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import DEFAULT_DB_PATH, connect
from bakery.persistence.repositories import list_active_payment_methods

API_HOST = "127.0.0.1"
API_PORT = 8765


class SaleLineCreate(BaseModel):
    """Subtotal lo calcula el backend; no se acepta en el cuerpo."""

    model_config = ConfigDict(extra="forbid")

    id_producto: int
    cantidad: int
    precio_aplicado: int


class SaleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_medio_pago: int
    lineas: List[SaleLineCreate] = Field(min_length=1)


class SaleResponse(BaseModel):
    id_venta: str
    valor_total: int
    fecha_venta: str
    id_medio_pago: int
    caja: int
    tendero: int


class PaymentMethodResponse(BaseModel):
    id_medio_pago: int
    nombre: str
    id_estado: int


class CategoryResponse(BaseModel):
    id_categoria: int
    nombre: str


class ProductCreate(BaseModel):
    nombre: str
    precio: int
    id_categoria: int
    descripcion: Optional[str] = None


class ProductUpdate(BaseModel):
    nombre: str
    precio: int
    id_categoria: int
    descripcion: Optional[str] = None


class ProductResponse(BaseModel):
    id_producto: int
    nombre: str
    precio: int
    id_categoria: int
    descripcion: Optional[str] = None
    id_estado: int


def create_app(db_path: Path = DEFAULT_DB_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize(db_path)
        app.state.db_path = db_path
        yield

    app = FastAPI(title="Bakery local API", lifespan=lifespan)
    app.state.db_path = db_path

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/medios-pago", response_model=List[PaymentMethodResponse])
    def get_payment_methods() -> List[dict]:
        connection = connect(app.state.db_path)
        try:
            return list_active_payment_methods(connection)
        finally:
            connection.close()

    @app.post("/ventas", response_model=SaleResponse)
    async def create_sale(request: Request) -> dict:
        payload: Any = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=400, detail="Cuerpo de venta inválido."
            )
        if "lineas" not in payload:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Debe enviar lineas de producto. "
                    "El cuerpo solo con valor_total ya no es válido."
                ),
            )
        try:
            body = SaleCreate.model_validate(payload)
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        connection = connect(app.state.db_path)
        try:
            return dict(
                register_sale(
                    connection,
                    body.id_medio_pago,
                    [line.model_dump() for line in body.lineas],
                )
            )
        except SaleValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    @app.get("/categorias", response_model=List[CategoryResponse])
    def get_categories() -> List[dict]:
        connection = connect(app.state.db_path)
        try:
            return list_categories(connection)
        finally:
            connection.close()

    @app.get("/productos", response_model=List[ProductResponse])
    def get_products() -> List[dict]:
        connection = connect(app.state.db_path)
        try:
            return list_all_products(connection)
        finally:
            connection.close()

    @app.get("/productos/activos", response_model=List[ProductResponse])
    def get_active_products(
        id_categoria: Optional[int] = Query(default=None),
        precio: Optional[int] = Query(default=None),
    ) -> List[dict]:
        connection = connect(app.state.db_path)
        try:
            return list_active_products(
                connection, id_categoria=id_categoria, precio=precio
            )
        except ProductValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    @app.get("/productos/{id_producto}", response_model=ProductResponse)
    def get_product_by_id(id_producto: int) -> dict:
        connection = connect(app.state.db_path)
        try:
            return dict(get_product(connection, id_producto))
        except ProductValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    @app.post("/productos", response_model=ProductResponse)
    def post_product(body: ProductCreate) -> dict:
        connection = connect(app.state.db_path)
        try:
            return dict(
                create_product(
                    connection,
                    nombre=body.nombre,
                    precio=body.precio,
                    id_categoria=body.id_categoria,
                    descripcion=body.descripcion,
                )
            )
        except ProductValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    @app.put("/productos/{id_producto}", response_model=ProductResponse)
    def put_product(id_producto: int, body: ProductUpdate) -> dict:
        connection = connect(app.state.db_path)
        try:
            return dict(
                update_product(
                    connection,
                    id_producto,
                    nombre=body.nombre,
                    precio=body.precio,
                    id_categoria=body.id_categoria,
                    descripcion=body.descripcion,
                )
            )
        except ProductValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    @app.post("/productos/{id_producto}/activar", response_model=ProductResponse)
    def post_activate_product(id_producto: int) -> dict:
        connection = connect(app.state.db_path)
        try:
            return dict(activate_product(connection, id_producto))
        except ProductValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    @app.post("/productos/{id_producto}/desactivar", response_model=ProductResponse)
    def post_deactivate_product(id_producto: int) -> dict:
        connection = connect(app.state.db_path)
        try:
            return dict(deactivate_product(connection, id_producto))
        except ProductValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    return app
