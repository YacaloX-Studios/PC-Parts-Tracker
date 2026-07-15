"""
PC Parts Tracker - Proveedor API MercadoLibre

Usa la API oficial REST de MercadoLibre en vez de scraping.
Requiere registrar una app en developers.mercadolibre.com
y obtener client_id + client_secret.

Flujo OAuth2:
  1. Usuario hace clic en "Sesion ML"
  2. Se abre navegador con URL de autorizacion
  3. Usuario autoriza la app
  4. ML redirige a localhost con un code
  5. Se intercambia code por access_token
  6. Se usa access_token para consultar precios
"""

import json
import re
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import webbrowser

import requests

from providers.base import Provider
from utils.logger import get_logger

logger = get_logger("providers.mercadolibre_api")

TOKEN_FILE = Path(__file__).parent.parent / "cache" / "ml_api_token.json"
SETTINGS_FILE = Path(__file__).parent.parent / "config.json"

API_BASE = "https://api.mercadolibre.com"
AUTH_BASE = "https://auth.mercadolibre.com.co"
REDIRECT_PORT = 18932
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"


class _OAuthHandler(BaseHTTPRequestHandler):
    """Handler minimalista para capturar el code de OAuth."""

    code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            _OAuthHandler.code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Autorizacion exitosa!</h2>"
                b"<p>Puedes cerrar esta ventana.</p></body></html>"
            )
        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            error = params.get("error_description", ["Error desconocido"])[0]
            self.wfile.write(f"<html><body><h2>Error: {error}</h2></body></html>".encode())

    def log_message(self, format, *args):
        pass


class MercadoLibreAPIProvider(Provider):
    """Proveedor que usa la API oficial de MercadoLibre."""

    DOMAINS = ["mercadolibre.com", "mercadolibre.com.co"]

    def __init__(self) -> None:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._token_data = self._load_token()
        self._blocked = False

    @property
    def name(self) -> str:
        return "MercadoLibre API"

    def matches_url(self, url: str) -> bool:
        return any(d in url.lower() for d in self.DOMAINS)

    def get_settings(self) -> dict:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_client_id(self) -> str:
        return self.get_settings().get("ml_client_id", "")

    def get_client_secret(self) -> str:
        return self.get_settings().get("ml_client_secret", "")

    def has_session(self) -> bool:
        return self._token_data is not None and self._is_token_valid()

    def login(self) -> bool:
        """Flujo OAuth2 completo: abre navegador, captura code, obtiene token."""
        client_id = self.get_client_id()
        client_secret = self.get_client_secret()

        if not client_id or not client_secret:
            logger.error("Falta ml_client_id o ml_client_secret en config.json")
            return False

        auth_url = (
            f"{AUTH_BASE}/authorization"
            f"?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={REDIRECT_URI}"
        )

        _OAuthHandler.code = None

        server = HTTPServer(("localhost", REDIRECT_PORT), _OAuthHandler)
        server_thread = threading.Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        webbrowser.open(auth_url)
        logger.info("Navegador abierto para autorizacion ML...")

        server_thread.join(timeout=300)
        server.server_close()

        if not _OAuthHandler.code:
            logger.warning("No se recibio codigo de autorizacion")
            return False

        logger.info("Codigo de autorizacion recibido")

        try:
            resp = requests.post(
                f"{API_BASE}/oauth/token",
                json={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": _OAuthHandler.code,
                    "redirect_uri": REDIRECT_URI,
                },
                timeout=15,
            )
            resp.raise_for_status()
            token_data = resp.json()

            token_data["obtained_at"] = time.time()
            self._save_token(token_data)
            self._token_data = token_data

            logger.info("Token obtenido y guardado")
            return True
        except Exception as e:
            logger.error("Error obteniendo token: %s", e)
            return False

    def logout(self) -> None:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
        self._token_data = None
        logger.info("Sesion API eliminada")

    def get_price(self, url: str, headless: bool = True) -> float | None:
        if self._blocked:
            return None

        item_id = self._extract_item_id(url)
        if not item_id:
            logger.warning("No se pudo extraer item_id de: %s", url)
            return None

        logger.info("API: consultando item %s", item_id)

        try:
            headers = {"User-Agent": "PCPartsTracker/1.0"}
            if self._token_data and self._is_token_valid():
                headers["Authorization"] = f"Bearer {self._token_data['access_token']}"

            resp = requests.get(
                f"{API_BASE}/items/{item_id}",
                headers=headers,
                timeout=15,
            )

            if resp.status_code == 404:
                logger.warning("Item no encontrado: %s", item_id)
                return None

            if resp.status_code == 401:
                logger.warning("Token expirado, intentando refrescar...")
                if self._refresh_token():
                    headers["Authorization"] = f"Bearer {self._token_data['access_token']}"
                    resp = requests.get(
                        f"{API_BASE}/items/{item_id}",
                        headers=headers,
                        timeout=15,
                    )
                else:
                    self._blocked = True
                    return None

            if resp.status_code == 403:
                logger.warning("Acceso denegado para item %s (inicia sesion)", item_id)
                self._blocked = True
                return None

            resp.raise_for_status()
            data = resp.json()

            price = data.get("price")
            if price is not None:
                price = float(price)
                title = data.get("title", "?")[:50]
                logger.info("Precio API: %s = %s | %s", item_id, f"{price:,.0f}", title)
                return price if price > 0 else None

            logger.warning("Sin precio en respuesta API: %s", item_id)
            return None

        except requests.RequestException as e:
            logger.error("Error API: %s", e)
            return None

    def reset_block(self) -> None:
        self._blocked = False

    def _extract_item_id(self, url: str) -> str | None:
        """Extrae el item_id de una URL de MercadoLibre."""
        patterns = [
            r"/p/(MCO\d+)",
            r"/(MCO\d+)(?:\?|$)",
            r"MCO-(\d+)",
            r"(MCO\d{8,})",
        ]
        for pattern in patterns:
            m = re.search(pattern, url)
            if m:
                item_id = m.group(1)
                if not item_id.startswith("MCO"):
                    item_id = "MCO" + item_id
                return item_id

        parts = url.rstrip("/").split("/")
        for part in reversed(parts):
            if part.startswith("MCO") and len(part) > 6:
                return part.split("-")[0] if "-" in part and part.split("-")[0].startswith("MCO") else part
            m = re.match(r"(MCO\d+)", part)
            if m:
                return m.group(1)

        return None

    def _is_token_valid(self) -> bool:
        if not self._token_data:
            return False
        obtained = self._token_data.get("obtained_at", 0)
        expires_in = self._token_data.get("expires_in", 0)
        return (time.time() - obtained) < (expires_in - 60)

    def _refresh_token(self) -> bool:
        if not self._token_data or "refresh_token" not in self._token_data:
            return False

        client_id = self.get_client_id()
        client_secret = self.get_client_secret()

        try:
            resp = requests.post(
                f"{API_BASE}/oauth/token",
                json={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": self._token_data["refresh_token"],
                },
                timeout=15,
            )
            resp.raise_for_status()
            token_data = resp.json()
            token_data["obtained_at"] = time.time()
            self._save_token(token_data)
            self._token_data = token_data
            logger.info("Token refrescado")
            return True
        except Exception as e:
            logger.error("Error refrescando token: %s", e)
            return False

    def _load_token(self) -> dict | None:
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return None
        return None

    def _save_token(self, data: dict) -> None:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
