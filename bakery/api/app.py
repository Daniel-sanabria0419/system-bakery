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
from bakery.app.sales import (
    SaleNotEditableError,
    SaleNotFoundError,
    SaleValidationError,
    add_sale_observacion,
    get_sale_detail,
    list_sales,
    register_sale,
    update_sale,
)
from bakery.persistence import initialize
from bakery.persistence.connection import DEFAULT_DB_PATH, connect
from bakery.persistence.repositories import list_active_payment_methods

API_HOST = "127.0.0.1"
API_PORT = 8765


class SaleLineCreate(BaseModel):
    """Línea de venta. subtotal y total los calcula el backend; no se aceptan del cliente."""

    model_config = ConfigDict(extra="forbid")

    id_producto: int
    cantidad: int
    precio_aplicado: int


class SaleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_venta: str
    id_medio_pago: int
    lineas: List[SaleLineCreate] = Field(min_length=1)
    observacion: Optional[str] = None


class SaleUpdate(BaseModel):
    """Edición dentro de 1 h. Sin fecha_venta / totales del cliente (extra forbid)."""

    model_config = ConfigDict(extra="forbid")

    id_medio_pago: int
    lineas: List[SaleLineCreate] = Field(default_factory=list)
    observacion_venta: Optional[str] = None


class SaleObservacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str


class SaleResponse(BaseModel):
    id_venta: str
    valor_total: int
    fecha_venta: str
    id_medio_pago: int
    caja: int
    tendero: int


class SaleListItemResponse(BaseModel):
    id_venta: str
    valor_total: int
    fecha_venta: str
    id_medio_pago: int
    nombre_medio: str
    caja: int
    tendero: int
    cantidad_lineas: int
    es_legado: bool
    editable: bool


class SaleLineDetailResponse(BaseModel):
    id_linea: int
    id_venta: str
    id_producto: int
    nombre_producto: str
    precio_aplicado: int
    cantidad: int
    subtotal: int
    total: int
    id_promocion: Optional[int] = None
    nombre_promocion: Optional[str] = None


class SaleObservacionResponse(BaseModel):
    id_observacion: int
    id_venta: str
    texto: str
    origen: str
    fecha_creacion: str
    id_cambio: Optional[int] = None


class SaleDetailResponse(BaseModel):
    id_venta: str
    valor_total: int
    fecha_venta: str
    id_medio_pago: int
    nombre_medio: str
    caja: int
    tendero: int
    lineas: List[SaleLineDetailResponse]
    observaciones: List[SaleObservacionResponse]
    es_legado: bool
    editable: bool


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
    ruta_imagen: Optional[str] = None


class ProductUpdate(BaseModel):
    nombre: str
    precio: int
    id_categoria: int
    descripcion: Optional[str] = None
    ruta_imagen: Optional[str] = None
    actualizar_ruta_imagen: bool = False


class ProductResponse(BaseModel):
    id_producto: int
    nombre: str
    precio: int
    id_categoria: int
    descripcion: Optional[str] = None
    id_estado: int
    ruta_imagen: Optional[str] = None
    promocion_id: Optional[int] = None
    promocion_tipo: Optional[str] = None
    promocion_configuracion: Optional[str] = None
    promocion_activo: Optional[int] = None


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
                    id_venta=body.id_venta,
                    observacion=body.observacion,
                )
            )
        except SaleValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    @app.get("/ventas", response_model=List[SaleListItemResponse])
    def get_ventas() -> List[dict]:
        connection = connect(app.state.db_path)
        try:
            return [dict(row) for row in list_sales(connection)]
        finally:
            connection.close()

    @app.get("/ventas/{id_venta}", response_model=SaleDetailResponse)
    def get_venta_by_id(id_venta: str) -> dict:
        connection = connect(app.state.db_path)
        try:
            detail = get_sale_detail(connection, id_venta)
            if detail is None:
                raise HTTPException(status_code=404, detail="Venta no encontrada.")
            return dict(detail)
        finally:
            connection.close()

    @app.put("/ventas/{id_venta}", response_model=SaleResponse)
    async def put_venta(id_venta: str, request: Request) -> dict:
        payload: Any = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=400, detail="Cuerpo de venta inválido."
            )
        try:
            body = SaleUpdate.model_validate(payload)
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        connection = connect(app.state.db_path)
        try:
            return dict(
                update_sale(
                    connection,
                    id_venta,
                    body.id_medio_pago,
                    [line.model_dump() for line in body.lineas],
                    observacion_venta=body.observacion_venta,
                )
            )
        except SaleNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except SaleNotEditableError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except SaleValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    @app.post(
        "/ventas/{id_venta}/observaciones",
        response_model=SaleObservacionResponse,
    )
    def post_venta_observacion(
        id_venta: str, body: SaleObservacionCreate
    ) -> dict:
        connection = connect(app.state.db_path)
        try:
            return dict(add_sale_observacion(connection, id_venta, body.texto))
        except SaleNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
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
        precio: Optional[int] = Query(
            default=None,
            description=(
                "Legado: filtro por precio exacto. El desktop de cobro no lo usa."
            ),
        ),
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
                    ruta_imagen=body.ruta_imagen,
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
                    ruta_imagen=body.ruta_imagen,
                    actualizar_ruta_imagen=body.actualizar_ruta_imagen,
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
