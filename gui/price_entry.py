"""
PC Parts Tracker - Ingreso Manual de Precios

Ventana para ingresar/editar precios de todos los productos
de una sola vez, tipo hoja de calculo.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from utils.logger import get_logger

logger = get_logger("gui.price_entry")


class PriceEntryWindow(ctk.CTkToplevel):
    """Ventana para ingresar precios manualmente."""

    def __init__(self, parent, product_repo, history_repo) -> None:
        super().__init__(parent)

        self._product_repo = product_repo
        self._history_repo = history_repo
        self._entries: dict[int, ctk.CTkEntry] = {}

        self.title("Ingresar Precios Manualmente")
        self.geometry("700x550")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 700) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 550) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()
        self._load_products()

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, height=50, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            header,
            text="Ingresa el precio actual de cada producto",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Precios en COP",
            font=ctk.CTkFont(size=12),
            text_color="#888",
        ).pack(side="right")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        table_header = ctk.CTkFrame(scroll, fg_color="#333", corner_radius=6)
        table_header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(table_header, text="Producto", width=280, anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 5), pady=6)
        ctk.CTkLabel(table_header, text="Categoria", width=100, anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=5, pady=6)
        ctk.CTkLabel(table_header, text="Precio Actual", width=120, anchor="e",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=5, pady=6)
        ctk.CTkLabel(table_header, text="Nuevo Precio", width=120, anchor="e",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(5, 10), pady=6)

        self._table_frame = scroll

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=120, fg_color="#555",
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Guardar Todos", width=150, fg_color="#2fa572",
            command=self._save_all,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame, text="Limpiar Todo", width=120, fg_color="#d9534f",
            command=self._clear_all,
        ).pack(side="right", padx=(0, 10))

    def _load_products(self) -> None:
        products = self._product_repo.get_all(active_only=True)

        for product in products:
            row = ctk.CTkFrame(self._table_frame, fg_color="transparent", height=36)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=product.name, width=280, anchor="w",
                         font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 5))
            ctk.CTkLabel(row, text=product.category or "-", width=100, anchor="w",
                         font=ctk.CTkFont(size=11), text_color="#aaa").pack(side="left", padx=5)

            current_text = f"${product.current_price:,.0f}" if product.current_price else "-"
            ctk.CTkLabel(row, text=current_text, width=120, anchor="e",
                         font=ctk.CTkFont(size=12)).pack(side="left", padx=5)

            entry_var = ctk.StringVar(value="")
            entry = ctk.CTkEntry(row, textvariable=entry_var, width=120, justify="right",
                                 placeholder_text="...")
            entry.pack(side="left", padx=(5, 10))

            self._entries[product.id] = (entry_var, product.current_price)

    def _clear_all(self) -> None:
        for entry_var, _ in self._entries.values():
            entry_var.set("")

    def _save_all(self) -> None:
        updated = 0
        errors = []

        for product_id, (entry_var, old_price) in self._entries.items():
            raw = entry_var.get().strip()
            if not raw:
                continue

            try:
                clean = raw.replace("$", "").replace(".", "").replace(",", "").strip()
                new_price = float(clean)
                if new_price <= 0:
                    errors.append(f"ID {product_id}: precio invalido ({raw})")
                    continue
            except ValueError:
                errors.append(f"ID {product_id}: no es un numero ({raw})")
                continue

            if old_price is not None and new_price == old_price:
                continue

            product = self._product_repo.get_by_id(product_id)
            if product:
                self._product_repo.update_price(product_id, new_price)
                self._history_repo.add_record(product_id, new_price)
                updated += 1
                logger.info("Precio actualizado: %s = %s", product.name, f"{new_price:,.0f}")

        msg = f"{updated} precios actualizados."
        if errors:
            msg += f"\n\nErrores:\n" + "\n".join(errors[:10])

        messagebox.showinfo("Resultado", msg)
        self.event_generate("<<PricesUpdated>>")
        self.destroy()
