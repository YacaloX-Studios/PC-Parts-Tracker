"""
PC Parts Tracker - Proveedor MercadoLibre

Scraping de precios usando Playwright.
Soporte para login manual del usuario via ventana del navegador.
"""

import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from providers.base import Provider
from utils.logger import get_logger

logger = get_logger("providers.mercadolibre")

SESSION_FILE = Path(__file__).parent.parent / "cache" / "ml_session.json"


class MercadoLibreProvider(Provider):
    """Proveedor de precios para MercadoLibre Colombia."""

    DOMAINS = ["mercadolibre.com", "mercadolibre.com.co"]

    def __init__(self) -> None:
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._blocked = False

    @property
    def name(self) -> str:
        return "MercadoLibre"

    def matches_url(self, url: str) -> bool:
        return any(d in url.lower() for d in self.DOMAINS)

    def has_session(self) -> bool:
        return SESSION_FILE.exists()

    def login(self) -> bool:
        """
        Abre una ventana del navegador para que el usuario inicie sesión.
        Al cerrar la ventana, se guardan las cookies de sesión.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                )

                ctx = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                    locale="es-CO",
                )
                page = ctx.new_page()

                page.goto("https://www.mercadolibre.com.co", wait_until="domcontentloaded")
                logger.info("Ventana de login abierta - esperando que el usuario inicie sesión...")

                page.wait_for_event("close", timeout=0)

                try:
                    storage = ctx.storage_state()
                    with open(SESSION_FILE, "w", encoding="utf-8") as f:
                        json.dump(storage, f, indent=2)
                    logger.info("Sesion guardada: %s", SESSION_FILE)
                except Exception as e:
                    logger.error("Error guardando sesion: %s", e)
                finally:
                    browser.close()

                return SESSION_FILE.exists()
        except Exception as e:
            logger.error("Error en login: %s", e)
            return False

    def get_price(self, url: str, headless: bool = True) -> float | None:
        if self._blocked:
            logger.debug("Bloqueado por ML, saltando: %s", url)
            return None

        logger.info("Scraping: %s", url)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                    ],
                )

                try:
                    ctx_opts = dict(
                        user_agent=(
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/125.0.0.0 Safari/537.36"
                        ),
                        viewport={"width": 1920, "height": 1080},
                        locale="es-CO",
                    )

                    if SESSION_FILE.exists():
                        try:
                            ctx = browser.new_context(storage_state=str(SESSION_FILE), **ctx_opts)
                            logger.info("Usando sesion guardada")
                        except Exception:
                            ctx = browser.new_context(**ctx_opts)
                            logger.warning("Sesion invalida, creando nueva")
                    else:
                        ctx = browser.new_context(**ctx_opts)

                    page = ctx.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_timeout(3000)

                    if self._is_blocked(page):
                        logger.warning("ML bloqueando (inicia sesion desde la app)")
                        self._blocked = True
                        return None

                    price = self._extract_from_meta(page)
                    if price:
                        logger.info("Precio (meta): %s", f"{price:,.0f}")
                        return price

                    price = self._extract_from_fraction(page)
                    if price:
                        logger.info("Precio (fraction): %s", f"{price:,.0f}")
                        return price

                    price = self._extract_from_json_ld(page)
                    if price:
                        logger.info("Precio (json-ld): %s", f"{price:,.0f}")
                        return price

                    logger.warning("Sin precio: %s", url)
                    return None
                finally:
                    ctx.close()
                    browser.close()
        except PlaywrightTimeout:
            logger.error("Timeout: %s", url)
            return None
        except Exception as e:
            logger.error("Error: %s", url, str(e))
            return None

    def reset_block(self) -> None:
        self._blocked = False

    def logout(self) -> None:
        """Elimina la sesion guardada."""
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
            logger.info("Sesion eliminada")

    def _is_blocked(self, page) -> bool:
        url = page.url.lower()
        if "account-verification" in url or "login" in url:
            return True
        try:
            body = page.inner_text("body")[:300].lower()
            return "ingresa a tu cuenta" in body or "ya tengo cuenta" in body
        except Exception:
            return False

    def _extract_from_meta(self, page) -> float | None:
        try:
            meta = page.query_selector('meta[itemprop="price"]')
            if meta:
                content = meta.get_attribute("content")
                if content:
                    return self._parse_price(content)
        except Exception:
            pass
        return None

    def _extract_from_fraction(self, page) -> float | None:
        try:
            el = page.query_selector(".andes-money-amount__fraction")
            if el:
                return self._parse_price(el.inner_text())
        except Exception:
            pass
        return None

    def _extract_from_json_ld(self, page) -> float | None:
        try:
            for s in page.query_selector_all('script[type="application/ld+json"]'):
                txt = s.inner_text()
                if "price" in txt:
                    m = re.search(r'"price"\s*:\s*"?(\d+[\d.,]*)"?', txt)
                    if m:
                        return self._parse_price(m.group(1))
        except Exception:
            pass
        return None

    @staticmethod
    def _parse_price(raw: str) -> float | None:
        try:
            if "-" in raw:
                return None
            cleaned = re.sub(r"[^\d.,]", "", raw.strip())
            if not cleaned:
                return None
            if "," in cleaned and "." in cleaned:
                if cleaned.rindex(",") > cleaned.rindex("."):
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    cleaned = cleaned.replace(",", "")
            elif "." in cleaned:
                parts = cleaned.split(".")
                if len(parts[-1]) == 3 and len(parts) > 1:
                    cleaned = cleaned.replace(".", "")
            elif "," in cleaned:
                parts = cleaned.split(",")
                if len(parts[-1]) == 3 and len(parts) > 1:
                    cleaned = cleaned.replace(",", "")
                else:
                    cleaned = cleaned.replace(",", ".")
            price = float(cleaned.replace(" ", ""))
            return price if price > 0 else None
        except (ValueError, TypeError):
            return None
