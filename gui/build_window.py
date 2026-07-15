"""
PC Parts Tracker - Ventana de Builds (PCs Completas)

Gestión de configuraciones de PC completas con totales y ahorro.
"""

import customtkinter as ctk
from services.build_service import BuildService
from repositories.product_repository import ProductRepository
from database.models import Product
from utils.logger import get_logger

logger = get_logger("gui.build_window")


class BuildWindow(ctk.CTkToplevel):
    """Ventana para gestionar builds/PCs completas."""

    def __init__(
        self,
        parent,
        build_service: BuildService,
        product_repo: ProductRepository,
    ) -> None:
        super().__init__(parent)

        self._build_service = build_service
        self._product_repo = product_repo

        self.title("Mis Builds")
        self.geometry("900x600")
        self.minsize(800, 500)
        self.transient(parent)

        self._center_window()
        self._build_ui()
        self._load_builds()

    def _center_window(self) -> None:
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = self.master.winfo_x() + (self.master.winfo_width() - w) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            header, text="Mis Builds", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="+ Nuevo Build",
            width=140,
            height=35,
            command=self._create_build_dialog,
        ).pack(side="right")

        left_panel = ctk.CTkFrame(self, width=280)
        left_panel.pack(side="left", fill="y", padx=(15, 5), pady=(0, 15))
        left_panel.pack_propagate(False)

        ctk.CTkLabel(
            left_panel, text="Builds", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))

        self._build_list = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self._build_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self._build_detail_frame = ctk.CTkFrame(self)
        self._build_detail_frame.pack(
            side="right", fill="both", expand=True, padx=(5, 15), pady=(0, 15)
        )

        self._detail_title = ctk.CTkLabel(
            self._build_detail_frame,
            text="Selecciona un build",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self._detail_title.pack(pady=(15, 10))

        self._detail_content = ctk.CTkFrame(self._build_detail_frame, fg_color="transparent")
        self._detail_content.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self._selected_build_id: int | None = None

    def _load_builds(self) -> None:
        """Carga la lista de builds."""
        for widget in self._build_list.winfo_children():
            widget.destroy()

        summaries = self._build_service.get_all_builds_summary()

        if not summaries:
            ctk.CTkLabel(
                self._build_list,
                text="No hay builds creados",
                text_color="gray",
            ).pack(pady=20)
            return

        for summary in summaries:
            btn = ctk.CTkButton(
                self._build_list,
                text=summary["name"],
                anchor="w",
                height=38,
                fg_color="transparent",
                hover_color=("#e0e0e0", "#3b3b3b"),
                text_color=("black", "white"),
                command=lambda bid=summary["id"]: self._select_build(bid),
            )
            btn.pack(fill="x", pady=2)

    def _select_build(self, build_id: int) -> None:
        """Selecciona un build y muestra sus detalles."""
        self._selected_build_id = build_id
        summary = self._build_service.get_build_summary(build_id)
        if not summary:
            return

        self._detail_title.configure(text=summary["name"])

        for widget in self._detail_content.winfo_children():
            widget.destroy()

        if not summary["items"]:
            ctk.CTkLabel(
                self._detail_content,
                text="Este build no tiene productos",
                text_color="gray",
            ).pack(pady=20)
            return

        headers_frame = ctk.CTkFrame(self._detail_content, fg_color="transparent")
        headers_frame.pack(fill="x", pady=(0, 5))

        for text, w in [("Categoria", 120), ("Producto", 250), ("Precio", 120)]:
            ctk.CTkLabel(
                headers_frame, text=text, width=w, anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="left", padx=(10, 0))

        items_frame = ctk.CTkFrame(self._detail_content, fg_color="transparent")
        items_frame.pack(fill="both", expand=True)

        for i, item in enumerate(summary["items"]):
            fg = "transparent" if i % 2 == 0 else ("#f0f0f0", "#2b2b2b")
            row = ctk.CTkFrame(items_frame, fg_color=fg, corner_radius=0)
            row.pack(fill="x", pady=1)

            ctk.CTkLabel(row, text=item["category"], width=120, anchor="w").pack(
                side="left", padx=(10, 0), pady=4
            )
            ctk.CTkLabel(row, text=item["name"], width=250, anchor="w").pack(
                side="left", padx=(10, 0), pady=4
            )
            ctk.CTkLabel(
                row,
                text=f"${item['current_price']:,.0f}",
                width=120,
                anchor="w",
                font=ctk.CTkFont(weight="bold"),
            ).pack(side="left", padx=(10, 0), pady=4)

        separator = ctk.CTkFrame(self._detail_content, height=2, fg_color="gray")
        separator.pack(fill="x", pady=10)

        totals_frame = ctk.CTkFrame(self._detail_content, fg_color="transparent")
        totals_frame.pack(fill="x")

        total_text = f"TOTAL: ${summary['total_current']:,.0f}"
        ctk.CTkLabel(
            totals_frame,
            text=total_text,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="e", padx=10)

        if summary["possible_savings"] > 0:
            savings_text = f"Ahorro posible: ${summary['possible_savings']:,.0f}"
            ctk.CTkLabel(
                totals_frame,
                text=savings_text,
                font=ctk.CTkFont(size=13),
                text_color="#2fa572",
            ).pack(anchor="e", padx=10, pady=(2, 0))

        bottom_frame = ctk.CTkFrame(self._detail_content, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            bottom_frame,
            text="Eliminar Build",
            width=130,
            height=32,
            fg_color="#d9534f",
            hover_color="#c9302c",
            command=lambda: self._delete_build(build_id),
        ).pack(side="left")

    def _create_build_dialog(self) -> None:
        """Abre diálogo para crear un nuevo build."""
        dialog = ctk.CTkInputDialog(
            text="Nombre del nuevo build:", title="Crear Build"
        )
        name = dialog.get_input()

        if not name or not name.strip():
            return

        products = self._product_repo.get_all(active_only=True)

        selection_dialog = BuildSelectionDialog(self, products)
        self.wait_window(selection_dialog)

        selected_ids = selection_dialog.result
        if not selected_ids:
            return

        self._build_service.create_build(name.strip(), selected_ids)
        self._load_builds()
        logger.info("Build creado: '%s' con %d productos", name, len(selected_ids))

    def _delete_build(self, build_id: int) -> None:
        """Elimina un build tras confirmación."""
        from tkinter import messagebox
        if messagebox.askyesno(
            "Confirmar", "¿Eliminar este build?", parent=self
        ):
            self._build_service.delete_build(build_id)
            self._selected_build_id = None
            self._detail_title.configure(text="Selecciona un build")
            for w in self._detail_content.winfo_children():
                w.destroy()
            self._load_builds()


class BuildSelectionDialog(ctk.CTkToplevel):
    """Diálogo para seleccionar productos para un build."""

    def __init__(self, parent, products: list[Product]) -> None:
        super().__init__(parent)

        self.title("Seleccionar Productos")
        self.geometry("500x450")
        self.transient(parent)
        self.grab_set()

        self._selected_ids: list[int] = []
        self._check_vars: dict[int, ctk.BooleanVar] = {}

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 450) // 2
        self.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            self, text="Selecciona los productos", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        for product in products:
            var = ctk.BooleanVar(value=False)
            self._check_vars[product.id] = var
            ctk.CTkCheckBox(
                scroll,
                text=f"{product.name} ({product.category})",
                variable=var,
                font=ctk.CTkFont(size=12),
            ).pack(fill="x", pady=2, padx=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=120, fg_color="#555",
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Aceptar", width=120, command=self._accept,
        ).pack(side="right")

    @property
    def result(self) -> list[int]:
        return self._selected_ids

    def _accept(self) -> None:
        self._selected_ids = [
            pid for pid, var in self._check_vars.items() if var.get()
        ]
        self.destroy()
