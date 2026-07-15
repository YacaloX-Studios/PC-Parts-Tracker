"""
PC Parts Tracker - Diálogo de Configuración

Preferencias de la aplicación: tema, caché, desarrollador, etc.
"""

import customtkinter as ctk
from utils.config import AppConfig
from utils.logger import get_logger

logger = get_logger("gui.settings_dialog")


class SettingsDialog(ctk.CTkToplevel):
    """Diálogo de configuración de la aplicación."""

    def __init__(self, parent, config: AppConfig, on_apply=None) -> None:
        super().__init__(parent)

        self._config = config
        self._on_apply = on_apply

        self.title("Configuracion")
        self.geometry("450x620")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 500) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            scroll, text="Configuracion", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 20))

        theme_frame = ctk.CTkFrame(scroll)
        theme_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            theme_frame, text="Tema de la interfaz",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self._theme_var = ctk.StringVar(value=self._config.appearance_mode)
        theme_row = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_row.pack(fill="x", padx=10, pady=(0, 10))

        for mode, text in [("dark", "Oscuro"), ("light", "Claro"), ("system", "Sistema")]:
            ctk.CTkRadioButton(
                theme_row, text=text, variable=self._theme_var, value=mode,
            ).pack(side="left", padx=(0, 15))

        cache_frame = ctk.CTkFrame(scroll)
        cache_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            cache_frame, text="Caché de precios",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        ttl_row = ctk.CTkFrame(cache_frame, fg_color="transparent")
        ttl_row.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(ttl_row, text="TTL (minutos):").pack(side="left")
        self._ttl_var = ctk.StringVar(value=str(self._config.cache_ttl_minutes))
        ctk.CTkEntry(ttl_row, textvariable=self._ttl_var, width=80).pack(side="left", padx=10)

        browser_frame = ctk.CTkFrame(scroll)
        browser_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            browser_frame, text="Navegador (Scraping)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self._headless_var = ctk.BooleanVar(value=self._config.browser_headless)
        ctk.CTkCheckBox(
            browser_frame,
            text="Modo headless (sin ventana del navegador)",
            variable=self._headless_var,
        ).pack(anchor="w", padx=10, pady=(0, 10))

        dev_frame = ctk.CTkFrame(scroll)
        dev_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            dev_frame, text="Desarrollador",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self._dev_var = ctk.BooleanVar(value=self._config.developer_mode)
        ctk.CTkCheckBox(
            dev_frame,
            text="Modo desarrollador (logs detallados en consola)",
            variable=self._dev_var,
        ).pack(anchor="w", padx=10, pady=(0, 10))

        backup_frame = ctk.CTkFrame(scroll)
        backup_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            backup_frame, text="Copia de Seguridad",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self._backup_var = ctk.BooleanVar(value=self._config.get("backup_on_exit", True))
        ctk.CTkCheckBox(
            backup_frame,
            text="Crear backup al cerrar la aplicacion",
            variable=self._backup_var,
        ).pack(anchor="w", padx=10, pady=(0, 10))

        ml_frame = ctk.CTkFrame(scroll)
        ml_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            ml_frame, text="API MercadoLibre",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            ml_frame, text="client_id:",
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=10, pady=(5, 0))
        self._ml_client_id_var = ctk.StringVar(value=self._config.get("ml_client_id", ""))
        ctk.CTkEntry(ml_frame, textvariable=self._ml_client_id_var, width=350).pack(
            anchor="w", padx=10, pady=(0, 5),
        )

        ctk.CTkLabel(
            ml_frame, text="client_secret:",
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=10, pady=(5, 0))
        self._ml_client_secret_var = ctk.StringVar(value=self._config.get("ml_client_secret", ""))
        ctk.CTkEntry(ml_frame, textvariable=self._ml_client_secret_var, width=350, show="*").pack(
            anchor="w", padx=10, pady=(0, 10),
        )

        ctk.CTkLabel(
            ml_frame,
            text="Obtener en developers.mercadolibre.com",
            font=ctk.CTkFont(size=10),
            text_color="#888",
        ).pack(anchor="w", padx=10, pady=(0, 10))

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=120, fg_color="#555",
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Guardar", width=120, command=self._save,
        ).pack(side="right")

    def _save(self) -> None:
        """Guarda la configuración."""
        try:
            ttl = int(self._ttl_var.get())
            if ttl < 1:
                ttl = 1
        except ValueError:
            ttl = 60

        self._config.set("appearance_mode", self._theme_var.get())
        self._config.set("cache_ttl_minutes", ttl)
        self._config.set("browser_headless", self._headless_var.get())
        self._config.set("developer_mode", self._dev_var.get())
        self._config.set("backup_on_exit", self._backup_var.get())
        self._config.set("ml_client_id", self._ml_client_id_var.get().strip())
        self._config.set("ml_client_secret", self._ml_client_secret_var.get().strip())

        ctk.set_appearance_mode(self._config.appearance_mode)

        logger.info("Configuracion guardada")

        if self._on_apply:
            self._on_apply()

        self.destroy()
