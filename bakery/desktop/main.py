import threading
import time

import httpx
import uvicorn
from PySide6.QtWidgets import QApplication

from bakery.api.app import API_HOST, API_PORT, create_app
from bakery.desktop.client import ApiClient
from bakery.desktop.ui import MainWindow

_WAIT_ATTEMPTS = 50
_WAIT_INTERVAL_SECONDS = 0.1


def _run_api() -> None:
    uvicorn.run(
        create_app(),
        host=API_HOST,
        port=API_PORT,
        log_level="warning",
    )


def wait_for_api() -> None:
    url = f"http://{API_HOST}:{API_PORT}/health"
    for _ in range(_WAIT_ATTEMPTS):
        try:
            response = httpx.get(url, timeout=0.2)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(_WAIT_INTERVAL_SECONDS)
    raise RuntimeError("La API local no arrancó a tiempo.")


def start_api_in_background() -> threading.Thread:
    thread = threading.Thread(target=_run_api, daemon=True)
    thread.start()
    wait_for_api()
    return thread


def create_window(api_client: ApiClient = None) -> MainWindow:
    client = api_client or ApiClient()
    return MainWindow(client)


def main() -> None:
    start_api_in_background()
    qt_app = QApplication([])
    window = create_window()
    window.show()
    qt_app.exec()
