"""
PC Parts Tracker - Diálogo de Producto

Formulario para agregar o editar productos.
Soporta detección automática de tienda por URL.
"""

import customtkinter as ctk
from database.models import Product
from utils.logger import get_logger

logger = get_logger("gui.product_dialog")


class ProductDialog(ctk.CTkToplevel):
    """Diálogo modal para crear/editar un producto."""

    def __init__(
        self,
        parent,
        categories: list[str],
        product: Product | None = None,
        on_save=None,
    ) -> None:
        """
        Args:
            parent: Ventana padre.
            categories: Lista de categorías disponibles.
            product: Producto a editar (None para crear nuevo).
            on_save: Callback al guardar (recibe el dict de datos).
        """
        super().__init__(parent)

        self._product = product
        self._on_save = on_save
        self._categories = categories
        self._result_data: dict | None = None

        self.title("Editar Producto" if product else "Agregar Producto")
        self.geometry("520x620")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._center_window()
        self._build_ui()

        if product:
            self._fill_data()

    def _center_window(self) -> None:
        """Centra el diálogo sobre la ventana padre."""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = self.master.winfo_x() + (self.master.winfo_width() - w) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Construye la interfaz del formulario."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title_label = ctk.CTkLabel(
            main_frame,
            text="Editar Producto" if self._product else "Nuevo Producto",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title_label.pack(pady=(0, 15))

        fields_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        fields_frame.pack(fill="x")

        self._name_var = ctk.StringVar()
        self._category_var = ctk.StringVar()
        self._brand_var = ctk.StringVar()
        self._model_var = ctk.StringVar()
        self._store_var = ctk.StringVar()
        self._url_var = ctk.StringVar()
        self._price_var = ctk.StringVar()
        self._target_var = ctk.StringVar()

        self._entries: dict[str, ctk.CTkEntry] = {}

        fields = [
            ("Nombre *", "name", self._name_var),
            ("Categoria", "category", None),
            ("Marca", "brand", self._brand_var),
            ("Modelo", "model", self._model_var),
            ("Tienda", "store", self._store_var),
            ("URL *", "url", self._url_var),
            ("Precio Actual", "price", self._price_var),
            ("Precio Objetivo", "target", self._target_var),
        ]

        for label_text, key, string_var in fields:
            row = ctk.CTkFrame(fields_frame, fg_color="transparent")
            row.pack(fill="x", pady=(0, 8))

            label = ctk.CTkLabel(row, text=label_text, width=120, anchor="w",
                                 font=ctk.CTkFont(size=13))
            label.pack(side="left")

            if key == "category":
                entry = ctk.CTkComboBox(
                    row,
                    values=self._categories,
                    variable=self._category_var,
                    width=330,
                    state="readonly",
                )
            else:
                entry = ctk.CTkEntry(row, textvariable=string_var, width=330)

            entry.pack(side="right")
            self._entries[key] = entry

        self._url_var.trace_add("write", self._on_url_changed)

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            width=140,
            height=38,
            fg_color="#555555",
            hover_color="#666666",
            command=self.destroy,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Guardar",
            width=140,
            height=38,
            command=self._save,
        ).pack(side="right")

    def _on_url_changed(self, *_args) -> None:
        """Detecta tienda automáticamente al cambiar la URL."""
        url = self._url_var.get().lower()
        if "mercadolibre" in url:
            self._store_var.set("MercadoLibre")
        elif "amazon" in url:
            self._store_var.set("Amazon")
        elif "amd.com" in url:
            self._store_var.set("AMD")
        elif "intel.com" in url:
            self._store_var.set("Intel")

    def _fill_data(self) -> None:
        """Rellena el formulario con los datos del producto existente."""
        if not self._product:
            return

        self._name_var.set(self._product.name or "")
        self._category_var.set(self._product.category or "")
        self._brand_var.set(self._product.brand or "")
        self._model_var.set(self._product.model or "")
        self._store_var.set(self._product.store or "")
        self._url_var.set(self._product.url or "")

        if self._product.current_price:
            self._price_var.set(str(int(self._product.current_price)))
        if self._product.target_price:
            self._target_var.set(str(int(self._product.target_price)))

    def _save(self) -> None:
        """Valida y guarda los datos del formulario."""
        name = self._name_var.get().strip()
        url = self._url_var.get().strip()

        if not name:
            self._show_error("El nombre es obligatorio.")
            return
        if not url:
            self._show_error("La URL es obligatoria.")
            return
        if not url.startswith("http"):
            self._show_error("La URL debe comenzar con http:// o https://")
            return

        price = None
        price_str = self._price_var.get().strip()
        if price_str:
            try:
                price = float(price_str.replace(",", "").replace(".", "").replace("$", ""))
            except ValueError:
                self._show_error("El precio no es un número válido.")
                return

        target = None
        target_str = self._target_var.get().strip()
        if target_str:
            try:
                target = float(target_str.replace(",", "").replace(".", "").replace("$", ""))
            except ValueError:
                self._show_error("El precio objetivo no es un número válido.")
                return

        self._result_data = {
            "name": name,
            "category": self._category_var.get() or "Sin categoria",
            "brand": self._brand_var.get().strip() or None,
            "model": self._model_var.get().strip() or None,
            "store": self._store_var.get().strip() or "Desconocida",
            "url": url,
            "current_price": price,
            "target_price": target,
        }

        logger.info("Producto guardado: %s", name)

        if self._on_save:
            self._on_save(self._result_data)

        self.destroy()

    def _show_error(self, message: str) -> None:
        """Muestra un mensaje de error."""
        from tkinter import messagebox
        messagebox.showerror("Error", message, parent=self)

    @property
    def result(self) -> dict | None:
        """Datos resultado del diálogo."""
        return self._result_data
