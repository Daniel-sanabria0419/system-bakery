from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bakery.app.sales import SaleValidationError, register_sale
from bakery.persistence import initialize
from bakery.persistence.connection import DEFAULT_DB_PATH, connect
from bakery.persistence.repositories import list_active_payment_methods

API_HOST = "127.0.0.1"
API_PORT = 8765


class SaleCreate(BaseModel):
    valor_total: int
    id_medio_pago: int


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
    def create_sale(body: SaleCreate) -> dict:
        connection = connect(app.state.db_path)
        try:
            return dict(
                register_sale(
                    connection,
                    body.valor_total,
                    body.id_medio_pago,
                )
            )
        except SaleValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        finally:
            connection.close()

    return app
