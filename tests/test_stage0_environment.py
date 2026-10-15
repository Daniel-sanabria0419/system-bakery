from fastapi.testclient import TestClient

from bakery.api.app import create_app
from bakery.desktop.main import create_window, wait_for_api


def test_create_app_health(tmp_path) -> None:
    with TestClient(create_app(tmp_path / "bakery.sqlite3")) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_create_window(qtbot) -> None:
    class _StubClient:
        request_count = 0

        def list_payment_methods(self):
            return []

        def create_sale(self, valor_total, id_medio_pago):
            raise AssertionError("No debe guardar en esta prueba.")

    window = create_window(api_client=_StubClient())
    qtbot.addWidget(window)
    assert window.windowTitle() == "Panadería"


def test_wait_for_api_times_out_when_server_down(monkeypatch) -> None:
    monkeypatch.setattr("bakery.desktop.main._WAIT_ATTEMPTS", 1)
    monkeypatch.setattr("bakery.desktop.main._WAIT_INTERVAL_SECONDS", 0)
    try:
        wait_for_api()
    except RuntimeError as error:
        assert "API local" in str(error)
    else:
        raise AssertionError("Se esperaba RuntimeError si la API no está en marcha.")
