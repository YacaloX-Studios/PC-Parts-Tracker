"""
PC Parts Tracker - Ventana de Historial de Precios

Muestra el historial de precios de un producto con gráfico matplotlib
y tabla de registros.
"""

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database.models import Product
from repositories.history_repository import HistoryRepository
from utils.logger import get_logger

logger = get_logger("gui.history_window")


class HistoryWindow(ctk.CTkToplevel):
    """Ventana que muestra el historial de precios de un producto."""

    def __init__(self, parent, product: Product, history_repo: HistoryRepository) -> None:
        super().__init__(parent)

        self._product = product
        self._history_repo = history_repo

        self.title(f"Historial - {product.name}")
        self.geometry("800x550")
        self.minsize(700, 450)
        self.transient(parent)

        self._center_window()
        self._build_ui()
        self._load_data()

    def _center_window(self) -> None:
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = self.master.winfo_x() + (self.master.winfo_width() - w) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            header,
            text=self._product.name,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=15, pady=(0, 5))

        self._stats_labels: dict[str, ctk.CTkLabel] = {}
        stats = [
            ("Actual", "current"),
            ("Minimo", "min"),
            ("Maximo", "max"),
            ("Promedio", "avg"),
        ]

        for text, key in stats:
            card = ctk.CTkFrame(stats_frame, corner_radius=8)
            card.pack(side="left", expand=True, fill="x", padx=(0, 8))

            ctk.CTkLabel(
                card, text=text, font=ctk.CTkFont(size=11), text_color="gray"
            ).pack(pady=(8, 0))

            label = ctk.CTkLabel(
                card, text="$0", font=ctk.CTkFont(size=16, weight="bold")
            )
            label.pack(pady=(2, 8))
            self._stats_labels[key] = label

        chart_frame = ctk.CTkFrame(self)
        chart_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self._figure = Figure(figsize=(7, 2.5), dpi=100)
        self._figure.set_facecolor("white")
        self._ax = self._figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._figure, master=chart_frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="x", padx=15, pady=(0, 15))

        headers = ["Fecha", "Precio"]
        for col, header_text in enumerate(headers):
            label = ctk.CTkLabel(
                table_frame,
                text=header_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=200,
            )
            label.grid(row=0, column=col, padx=10, pady=(8, 2), sticky="w")

        self._table_container = ctk.CTkScrollableFrame(
            table_frame, height=120, fg_color="transparent"
        )
        self._table_container.grid(
            row=1, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="ew"
        )

    def _load_data(self) -> None:
        """Carga y muestra los datos del historial."""
        records = self._history_repo.get_history(self._product.id)

        self._update_stats(records)
        self._update_chart(records)
        self._update_table(records)

    def _update_stats(self, records) -> None:
        """Actualiza las tarjetas de estadísticas."""
        if not records:
            return

        prices = [r.price for r in records]
        current = prices[0] if prices else 0
        minimum = min(prices)
        maximum = max(prices)
        average = sum(prices) / len(prices)

        def fmt(p):
            return f"${p:,.0f}"

        self._stats_labels["current"].configure(text=fmt(current))
        self._stats_labels["min"].configure(text=fmt(minimum))
        self._stats_labels["max"].configure(text=fmt(maximum))
        self._stats_labels["avg"].configure(text=fmt(average))

    def _update_chart(self, records) -> None:
        """Actualiza el gráfico de precios."""
        self._ax.clear()

        if not records:
            self._ax.text(
                0.5, 0.5, "Sin datos de historial",
                ha="center", va="center", fontsize=12, color="gray",
                transform=self._ax.transAxes,
            )
            self._canvas.draw()
            return

        sorted_records = sorted(records, key=lambda r: r.date)
        dates = [r.date for r in sorted_records]
        prices = [r.price for r in sorted_records]

        self._ax.plot(dates, prices, color="#1f77b4", linewidth=2, marker="o", markersize=4)
        self._ax.fill_between(dates, prices, alpha=0.1, color="#1f77b4")

        self._ax.set_title("Evolucion de Precio", fontsize=12, pad=10)
        self._ax.set_xlabel("")
        self._ax.set_ylabel("Precio", fontsize=10)
        self._ax.tick_params(axis="both", labelsize=8)

        self._ax.yaxis.set_major_formatter(
            lambda x, p: f"${x / 1000:.0f}K" if x >= 1000 else f"${x:.0f}"
        )

        self._figure.autofmt_xdate()
        self._figure.tight_layout()
        self._canvas.draw()

    def _update_table(self, records) -> None:
        """Actualiza la tabla de historial."""
        for widget in self._table_container.winfo_children():
            widget.destroy()

        if not records:
            ctk.CTkLabel(
                self._table_container,
                text="Sin registros",
                text_color="gray",
            ).pack(pady=10)
            return

        display_records = records[:50]

        for i, record in enumerate(display_records):
            fg_color = "transparent" if i % 2 == 0 else ("#f0f0f0", "#2b2b2b")

            row_frame = ctk.CTkFrame(self._table_container, fg_color=fg_color, corner_radius=0)
            row_frame.pack(fill="x", pady=1)

            date_str = record.date.strftime("%Y-%m-%d %H:%M")
            ctk.CTkLabel(
                row_frame, text=date_str, width=200, anchor="w",
                font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=10, pady=4)

            ctk.CTkLabel(
                row_frame, text=f"${record.price:,.0f}", width=200, anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="left", padx=10, pady=4)

        if len(records) > 50:
            ctk.CTkLabel(
                self._table_container,
                text=f"... y {len(records) - 50} registros mas",
                text_color="gray",
                font=ctk.CTkFont(size=11),
            ).pack(pady=5)
