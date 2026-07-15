"""
PC Parts Tracker - Servicio de Notificaciones

Framework preparado para notificaciones de precio.
Soporta: desktop (tkinter), email (SMTP), Discord (webhook).
Solo desktop está implementado por ahora.
"""

from database.models import Product
from utils.logger import get_logger

logger = get_logger("services.notification")


class NotificationService:
    """
    Servicio centralizado de notificaciones.

    Actualmente soporta notificaciones de escritorio (tkinner).
    Email y Discord están preparados como stubs para implementación futura.
    """

    def __init__(self) -> None:
        self._desktop_enabled = True
        self._email_config: dict = {}
        self._discord_webhook: str = ""

    def notify_price_drop(
        self,
        product: Product,
        old_price: float,
        new_price: float,
    ) -> None:
        """
        Envía una notificación cuando un producto baja de precio.

        Args:
            product: Producto con el nuevo precio.
            old_price: Precio anterior.
            new_price: Nuevo precio.
        """
        change_pct = ((new_price - old_price) / old_price) * 100 if old_price > 0 else 0

        message = (
            f"¡{product.name} bajó de precio!\n"
            f"Antes: ${old_price:,.0f}\n"
            f"Ahora: ${new_price:,.0f}\n"
            f"Cambio: {change_pct:+.1f}%"
        )

        if product.target_price and new_price <= product.target_price:
            message += (
                f"\n\n¡Alcanzó el precio objetivo!"
                f"\nObjetivo: ${product.target_price:,.0f}"
            )

        logger.info(
            "Notificación de precio: %s | %s -> %s",
            product.name,
            f"${old_price:,.0f}",
            f"${new_price:,.0f}",
        )

        self._send_desktop(message)

        if self._discord_webhook:
            self._send_discord(message)

        if self._email_config:
            self._send_email(
                subject=f"PC Parts Tracker: {product.name} bajó de precio",
                body=message,
            )

    def notify_target_reached(
        self,
        product: Product,
        current_price: float,
    ) -> None:
        """
        Notifica cuando un producto alcanza su precio objetivo.

        Args:
            product: Producto que alcanzó el objetivo.
            current_price: Precio actual.
        """
        message = (
            f"¡{product.name} alcanzó el precio objetivo!\n"
            f"Precio actual: ${current_price:,.0f}\n"
            f"Precio objetivo: ${product.target_price:,.0f}"
        )
        logger.info(
            "Alerta objetivo alcanzado: %s a %s",
            product.name,
            f"${current_price:,.0f}",
        )
        self._send_desktop(message)

    def _send_desktop(self, message: str) -> None:
        """Envía notificación de escritorio (popup)."""
        if not self._desktop_enabled:
            return
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("PC Parts Tracker", message)
            root.destroy()
        except Exception as e:
            logger.error("Error enviando notificación desktop: %s", e)

    def _send_discord(self, message: str) -> None:
        """
        Envía notificación a Discord via webhook.

        TODO: Implementar envío real con requests.post()
        Necesita: webhook URL configurada en config.json
        """
        # TODO: Implement Discord webhook
        # import requests
        # payload = {"content": message}
        # requests.post(self._discord_webhook, json=payload)
        logger.debug("Discord webhook (no implementado): %s", message[:50])

    def _send_email(self, subject: str, body: str) -> None:
        """
        Envía notificación por email via SMTP.

        TODO: Implementar envío real con smtplib
        Necesita: configuración SMTP en config.json
        """
        # TODO: Implement SMTP email
        # import smtplib
        # from email.mime.text import MIMEText
        # msg = MIMEText(body)
        # msg['Subject'] = subject
        # msg['From'] = self._email_config['from']
        # msg['To'] = self._email_config['to']
        # with smtplib.SMTP(self._email_config['smtp_server']) as server:
        #     server.send_message(msg)
        logger.debug("Email (no implementado): %s", subject)

    def configure_discord(self, webhook_url: str) -> None:
        """Configura la URL del webhook de Discord."""
        self._discord_webhook = webhook_url
        logger.info("Discord webhook configurado")

    def configure_email(self, config: dict) -> None:
        """
        Configura el envío de emails.

        Args:
            config: Dict con smtp_server, port, from, to, password.
        """
        self._email_config = config
        logger.info("Email configurado: %s", config.get("smtp_server", "N/A"))

    def set_desktop_enabled(self, enabled: bool) -> None:
        """Habilita/deshabilita notificaciones de escritorio."""
        self._desktop_enabled = enabled
