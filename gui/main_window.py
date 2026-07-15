"""
PC Parts Tracker - Ventana Principal

Interfaz principal de la aplicación con tabla de productos,
búsqueda, filtros y barra de herramientas.
"""

import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import ttk, messagebox

from database.database import Database
from repositories.product_repository import ProductRepository
from repositories.history_repository import HistoryRepository
from repositories.build_repository import BuildRepository
from providers.manager import ProviderManager
from providers.mercadolibre_api import MercadoLibreAPIProvider
from services.price_updater import PriceUpdater
from services.build_service import BuildService
from services.notification_service import NotificationService
from utils.config import AppConfig
from utils.cache import PriceCache
from utils.logger import get_logger, setup_logger
from utils.excel import ExcelManager
from gui.product_dialog import ProductDialog
from gui.price_entry import PriceEntryWindow
from gui.history_window import HistoryWindow
from gui.build_window import BuildWindow
from gui.settings_dialog import SettingsDialog

logger = get_logger("gui.main_window")


class MainWindow(ctk.CTk):
    """Ventana principal de PC Parts Tracker."""

    def __init__(self, config: AppConfig, db: Database) -> None:
        super().__init__()

        self._config = config
        self._db = db

        self.title("PC Parts Tracker")
        self.geometry(
            f"{config.get('window_width', 1200)}x{config.get('window_height', 700)}"
        )
        self.minsize(900, 500)

        icon_path = __import__("pathlib").Path(__file__).parent.parent / "pc_parts_tracker.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        ctk.set_appearance_mode(config.appearance_mode)
        ctk.set_default_color_theme(config.color_theme)

        self._setup_services()
        self._build_ui()
        self._load_products()
        self._update_status_bar()

    def _setup_services(self) -> None:
        """Inicializa todos los servicios y repositorios."""
        session = self._db.get_session()
        self._product_repo = ProductRepository(session)
        self._history_repo = HistoryRepository(session)
        self._build_repo = BuildRepository(session)

        self._provider_manager = ProviderManager()
        self._provider_manager.register(MercadoLibreAPIProvider())

        self._cache = PriceCache(ttl_minutes=self._config.cache_ttl_minutes)

        self._price_updater = PriceUpdater(
            self._product_repo,
            self._history_repo,
            self._provider_manager,
            self._cache,
        )
        self._build_service = BuildService(self._build_repo, self._product_repo)
        self._notification_service = NotificationService()
        self._excel_manager = ExcelManager()

    def _build_ui(self) -> None:
        """Construye la interfaz principal."""
        self._build_toolbar()
        self._build_table_area()
        self._build_bottom_bar()
        self._build_status_bar()

    def _build_toolbar(self) -> None:
        """Barra superior con búsqueda y filtros."""
        toolbar = ctk.CTkFrame(self, height=60, corner_radius=0)
        toolbar.pack(fill="x", padx=0, pady=0)
        toolbar.pack_propagate(False)

        title = ctk.CTkLabel(
            toolbar,
            text="PC Parts Tracker",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(side="left", padx=(20, 15), pady=10)

        search_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_frame.pack(side="left", fill="y", pady=10)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search_trace)
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text="Buscar producto...",
            width=280,
            height=35,
        )
        search_entry.pack(side="left")

        cat_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        cat_frame.pack(side="left", padx=(15, 0), fill="y", pady=10)

        ctk.CTkLabel(cat_frame, text="Categoria:").pack(side="left", padx=(0, 5))

        self._category_var = ctk.StringVar(value="Todas")
        categories = ["Todas"] + self._config.categories
        self._category_combo = ctk.CTkComboBox(
            cat_frame,
            values=categories,
            variable=self._category_var,
            width=150,
            height=35,
            state="readonly",
            command=lambda _: self._on_search(),
        )
        self._category_combo.pack(side="left")

        right_toolbar = ctk.CTkFrame(toolbar, fg_color="transparent")
        right_toolbar.pack(side="right", fill="y", pady=10)

        self._theme_btn = ctk.CTkButton(
            right_toolbar,
            text="Tema",
            width=70,
            height=35,
            fg_color="#555",
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            right_toolbar,
            text="Config",
            width=70,
            height=35,
            fg_color="#555",
            command=self._open_settings,
        ).pack(side="left")

    def _build_table_area(self) -> None:
        """Área central con la tabla de productos."""
        table_frame = ctk.CTkFrame(self, corner_radius=0)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(10, 0))

        columns = ("id", "name", "category", "store", "price", "change", "target", "updated")
        self._tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=20,
        )

        self._tree.heading("id", text="ID")
        self._tree.heading("name", text="Producto")
        self._tree.heading("category", text="Categoria")
        self._tree.heading("store", text="Tienda")
        self._tree.heading("price", text="Precio")
        self._tree.heading("change", text="Cambio")
        self._tree.heading("target", text="Objetivo")
        self._tree.heading("updated", text="Ultima Act.")

        self._tree.column("id", width=40, minwidth=40, stretch=False)
        self._tree.column("name", width=280, minwidth=150)
        self._tree.column("category", width=110, minwidth=90)
        self._tree.column("store", width=100, minwidth=80)
        self._tree.column("price", width=120, minwidth=100, anchor="e")
        self._tree.column("change", width=80, minwidth=70, anchor="center")
        self._tree.column("target", width=100, minwidth=80, anchor="e")
        self._tree.column("updated", width=120, minwidth=100)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=32, font=("Segoe UI", 11))
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._tree.bind("<Double-1>", lambda _: self._view_history())

    def _build_bottom_bar(self) -> None:
        """Barra inferior con botones de acción."""
        bottom = ctk.CTkFrame(self, height=60, corner_radius=0)
        bottom.pack(fill="x", padx=0, pady=(10, 0))
        bottom.pack_propagate(False)

        btn_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_frame.pack(expand=True)

        buttons = [
            ("Agregar", "#2fa572", self._add_product),
            ("Editar", "#1f77b4", self._edit_product),
            ("Eliminar", "#d9534f", self._delete_product),
            ("Abrir URL", "#1f77b4", self._open_url),
            ("Ingresar Precios", "#e87722", self._enter_prices),
            ("Importar Excel", "#20b2aa", self._reimport_excel),
            ("Ver Historial", "#5bc0de", self._view_history),
            ("Exportar", "#555", self._export_menu),
            ("Builds", "#9b59b6", self._open_builds),
        ]

        for text, color, cmd in buttons:
            ctk.CTkButton(
                btn_frame,
                text=text,
                width=130,
                height=36,
                fg_color=color,
                hover_color=color,
                font=ctk.CTkFont(size=12),
                command=cmd,
            ).pack(side="left", padx=4, pady=10)

    def _build_status_bar(self) -> None:
        """Barra de estado inferior."""
        self._status_bar = ctk.CTkFrame(self, height=28, corner_radius=0)
        self._status_bar.pack(fill="x", side="bottom")
        self._status_bar.pack_propagate(False)

        self._status_label = ctk.CTkLabel(
            self._status_bar, text="", font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._status_label.pack(side="left", padx=10)

        self._progress_label = ctk.CTkLabel(
            self._status_bar, text="", font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._progress_label.pack(side="right", padx=10)

    def _load_products(self, products=None) -> None:
        """Carga productos en la tabla."""
        for item in self._tree.get_children():
            self._tree.delete(item)

        if products is None:
            products = self._product_repo.get_all(active_only=True)

        for p in products:
            price_str = f"${p.current_price:,.0f}" if p.current_price else "---"

            change_str = "---"
            if p.price_change_pct is not None:
                pct = p.price_change_pct
                change_str = f"{pct:+.1f}%"
                if pct < 0:
                    change_str = f"\u2193 {abs(pct):.1f}%"
                elif pct > 0:
                    change_str = f"\u2191 {pct:.1f}%"

            target_str = f"${p.target_price:,.0f}" if p.target_price else "---"

            updated_str = ""
            if p.last_updated:
                updated_str = p.last_updated.strftime("%Y-%m-%d %H:%M")

            self._tree.insert(
                "",
                "end",
                iid=str(p.id),
                values=(
                    p.id,
                    p.name,
                    p.category,
                    p.store,
                    price_str,
                    change_str,
                    target_str,
                    updated_str,
                ),
            )

        self._update_status_bar()

    def _update_status_bar(self) -> None:
        """Actualiza la barra de estado."""
        count = self._product_repo.count(active_only=True)
        self._status_label.configure(text=f"Productos: {count}")

    def _on_search_trace(self, *_args) -> None:
        """Handler seguro para el trace de búsqueda."""
        try:
            self.after(150, self._on_search)
        except Exception:
            pass

    def _on_search(self) -> None:
        """Filtra productos por búsqueda y categoría."""
        query = self._search_var.get().strip()
        category = self._category_var.get()

        if query:
            products = self._product_repo.search(query)
        else:
            products = self._product_repo.get_all(active_only=True)

        if category and category != "Todas":
            products = [p for p in products if p.category == category]

        self._load_products(products)

    def _get_selected_id(self) -> int | None:
        """Obtiene el ID del producto seleccionado."""
        selection = self._tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _add_product(self) -> None:
        """Abre el diálogo para agregar un producto."""
        def on_save(data: dict):
            from database.models import Product as ProductModel
            product = ProductModel(
                name=data["name"],
                category=data["category"],
                brand=data["brand"],
                model=data["model"],
                store=data["store"],
                url=data["url"],
                current_price=data["current_price"],
                target_price=data["target_price"],
                lowest_price=data["current_price"],
                highest_price=data["current_price"],
            )
            self._product_repo.add(product)
            if data["current_price"]:
                self._history_repo.add_record(product.id, data["current_price"])
            self._load_products()

        ProductDialog(self, self._config.categories, on_save=on_save)

    def _edit_product(self) -> None:
        """Abre el diálogo para editar el producto seleccionado."""
        product_id = self._get_selected_id()
        if not product_id:
            messagebox.showwarning("Aviso", "Selecciona un producto primero.")
            return

        product = self._product_repo.get_by_id(product_id)
        if not product:
            return

        def on_save(data: dict):
            product.name = data["name"]
            product.category = data["category"]
            product.brand = data["brand"]
            product.model = data["model"]
            product.store = data["store"]
            product.url = data["url"]
            product.target_price = data["target_price"]
            if data["current_price"] is not None:
                product.current_price = data["current_price"]
            self._product_repo.update(product)
            self._load_products()

        ProductDialog(self, self._config.categories, product=product, on_save=on_save)

    def _delete_product(self) -> None:
        """Elimina el producto seleccionado."""
        product_id = self._get_selected_id()
        if not product_id:
            messagebox.showwarning("Aviso", "Selecciona un producto primero.")
            return

        product = self._product_repo.get_by_id(product_id)
        if not product:
            return

        if messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar '{product.name}'?\n\n"
            "El producto sera desactivado (no se eliminara permanentemente).",
        ):
            self._product_repo.delete(product_id)
            self._load_products()

    def _enter_prices(self) -> None:
        """Abre ventana de ingreso manual de precios."""
        win = PriceEntryWindow(self, self._product_repo, self._history_repo)
        win.bind("<<PricesUpdated>>", lambda _: self._load_products())

    def _open_url(self) -> None:
        """Abre la URL del producto seleccionado en el navegador."""
        import webbrowser
        product_id = self._get_selected_id()
        if not product_id:
            messagebox.showwarning("Aviso", "Selecciona un producto primero.")
            return
        product = self._product_repo.get_by_id(product_id)
        if not product or not product.url:
            messagebox.showwarning("Aviso", "Este producto no tiene URL.")
            return
        webbrowser.open(product.url)

    def _login_ml(self) -> None:
        """Inicia sesion via OAuth2 con la API de MercadoLibre."""
        ml_provider = None
        for prov in self._provider_manager._providers:
            if isinstance(prov, MercadoLibreAPIProvider):
                ml_provider = prov
                break

        if not ml_provider:
            return

        if not ml_provider.get_client_id() or not ml_provider.get_client_secret():
            messagebox.showwarning(
                "Configuracion ML",
                "Falta configurar client_id y client_secret.\n\n"
                "1. Ve a developers.mercadolibre.com\n"
                "2. Crea una app\n"
                "3. En Configuracion, ingresa los datos",
            )
            return

        if ml_provider.has_session():
            if messagebox.askyesno(
                "Sesion ML",
                "Ya hay una sesion guardada.\n\n"
                "¿Deseas cerrar sesion e iniciar una nueva?",
            ):
                ml_provider.logout()
            else:
                return

        self._progress_label.configure(text="Abriendo MercadoLibre para autorizar...")
        self.update_idletasks()

        def _run_login():
            try:
                success = ml_provider.login()
                if success:
                    ml_provider.reset_block()
                    self.after(0, lambda: messagebox.showinfo(
                        "Sesion ML",
                        "Sesion iniciada correctamente.\n"
                        "Ahora puedes usar 'Actualizar Precios'.",
                    ))
                else:
                    self.after(0, lambda: messagebox.showwarning(
                        "Sesion ML",
                        "No se pudo completar la autorizacion.",
                    ))
            except Exception as e:
                logger.error("Error en login ML: %s", e)
                self.after(0, lambda: messagebox.showerror("Error", f"Error: {e}"))
            finally:
                self.after(0, lambda: self._progress_label.configure(text=""))

        threading.Thread(target=_run_login, daemon=True).start()

    def _update_prices(self) -> None:
        """Inicia la actualización masiva de precios (scraping) en un hilo separado."""
        self._progress_label.configure(text="Actualizando precios...")
        self.update_idletasks()

        def _run_update():
            try:
                results = self._price_updater.update_all(
                    headless=self._config.browser_headless,
                    use_cache=True,
                )
                target_alerts = self._price_updater.check_target_prices()
                self.after(0, lambda: self._load_products())
                self.after(0, lambda: self._show_update_results(results, target_alerts))
            except Exception as e:
                logger.error("Error en actualización masiva: %s", e)
                self.after(0, lambda: messagebox.showerror("Error", f"Error actualizando: {e}"))
            finally:
                self.after(0, lambda: self._progress_label.configure(text=""))

        threading.Thread(target=_run_update, daemon=True).start()

    def _reimport_excel(self) -> None:
        """Importa productos desde el Excel seleccionado a la BD."""
        from tkinter import filedialog

        excel_path = filedialog.askopenfilename(
            title="Seleccionar Excel",
            filetypes=[("Excel", "*.xlsx *.xlsm"), ("Todos", "*.*")],
            initialdir=str(Path(__file__).parent.parent),
        )
        if not excel_path:
            return

        self._progress_label.configure(text="Importando productos desde Excel...")
        self.update_idletasks()

        def _run_import():
            try:
                from excel_to_json import convert_excel_to_json
                import json

                json_path = str(Path(__file__).parent.parent / "data" / "prices.json")
                products_data = convert_excel_to_json(excel_path, json_path)

                added = 0
                for item in products_data:
                    existing = self._product_repo.search(item["name"])
                    if not existing:
                        self._product_repo.create(
                            name=item["name"],
                            category=item["category"],
                            brand=item.get("brand", ""),
                            model=item.get("model", ""),
                            store=item["store"],
                            url=item.get("url", ""),
                            current_price=item.get("price"),
                            currency=item.get("currency", "COP"),
                        )
                        added += 1

                self.after(0, lambda: self._load_products())
                self.after(0, lambda: messagebox.showinfo(
                    "Importacion",
                    f"Importados {added} productos nuevos.\n"
                    f"Total en JSON: {len(products_data)}"
                ))
            except Exception as e:
                logger.error("Error importando Excel: %s", e)
                self.after(0, lambda: messagebox.showerror("Error", f"Error: {e}"))
            finally:
                self.after(0, lambda: self._progress_label.configure(text=""))

        threading.Thread(target=_run_import, daemon=True).start()

    def _show_update_results(self, results, target_alerts) -> None:
        """Muestra el resumen de la actualización."""
        successful = sum(1 for r in results if r.success)
        total = len(results)

        changes = []
        for r in results:
            if r.success and r.change_pct is not None:
                pct = r.change_pct
                arrow = "\u2193" if pct < 0 else "\u2191"
                changes.append(
                    f"{r.product_name}: {arrow}{abs(pct):.1f}% "
                    f"(${r.old_price:,.0f} -> ${r.new_price:,.0f})"
                )

        msg = f"Actualizacion completada: {successful}/{total} exitosas\n\n"
        if changes:
            msg += "Cambios:\n" + "\n".join(changes[:15])
            if len(changes) > 15:
                msg += f"\n... y {len(changes) - 15} mas"
        elif successful == 0 and total > 0:
            msg += (
                "MercadoLibre esta requiriendo autenticacion.\n\n"
                "Para solucionarlo:\n"
                "1. Abre MercadoLibre en tu navegador\n"
                "2. Inicia sesion\n"
                "3. Vuelve a intentar\n\n"
                "O puedes actualizar precios manualmente:\n"
                "Selecciona producto -> Editar -> Cambia el precio"
            )

        if target_alerts:
            msg += "\n\n--- ALERTAS DE PRECIO ---\n"
            for alert in target_alerts:
                msg += (
                    f"\n{alert['product'].name} alcanzo el objetivo: "
                    f"${alert['current_price']:,.0f}"
                )

        messagebox.showinfo("Resultado", msg)

    def _view_history(self) -> None:
        """Abre la ventana de historial del producto seleccionado."""
        product_id = self._get_selected_id()
        if not product_id:
            messagebox.showwarning("Aviso", "Selecciona un producto primero.")
            return

        product = self._product_repo.get_by_id(product_id)
        if not product:
            return

        HistoryWindow(self, product, self._history_repo)

    def _export_menu(self) -> None:
        """Muestra menú de exportación."""
        from tkinter import filedialog

        menu = ctk.CTkToplevel(self)
        menu.title("Exportar")
        menu.geometry("300x150")
        menu.transient(self)
        menu.grab_set()

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 300) // 2
        y = self.winfo_y() + (self.winfo_height() - 150) // 2
        menu.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            menu, text="Formato de exportacion", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10))

        products = self._product_repo.get_all(active_only=True)

        def export_excel():
            path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                title="Exportar como Excel",
            )
            if path:
                self._excel_manager.export_to_excel(products, path)
                messagebox.showinfo("Exportado", f"Guardado en:\n{path}")
            menu.destroy()

        def export_csv():
            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv")],
                title="Exportar como CSV",
            )
            if path:
                self._excel_manager.export_to_csv(products, path)
                messagebox.showinfo("Exportado", f"Guardado en:\n{path}")
            menu.destroy()

        btn_frame = ctk.CTkFrame(menu, fg_color="transparent")
        btn_frame.pack(pady=(0, 15))

        ctk.CTkButton(btn_frame, text="Excel (.xlsx)", width=120, command=export_excel).pack(
            side="left", padx=5
        )
        ctk.CTkButton(btn_frame, text="CSV", width=120, command=export_csv).pack(
            side="left", padx=5
        )

    def _open_builds(self) -> None:
        """Abre la ventana de builds."""
        BuildWindow(self, self._build_service, self._product_repo)

    def _open_settings(self) -> None:
        """Abre el diálogo de configuración."""
        def on_apply():
            self._cache = PriceCache(ttl_minutes=self._config.cache_ttl_minutes)
            self._price_updater = PriceUpdater(
                self._product_repo,
                self._history_repo,
                self._provider_manager,
                self._cache,
            )

        SettingsDialog(self, self._config, on_apply=on_apply)

    def _toggle_theme(self) -> None:
        """Alterna entre tema oscuro y claro."""
        current = self._config.appearance_mode
        new_mode = "light" if current == "dark" else "dark"
        self._config.set("appearance_mode", new_mode)
        ctk.set_appearance_mode(new_mode)

    def _on_close(self) -> None:
        """Maneja el cierre de la aplicación."""
        if self._config.get("backup_on_exit", True):
            self._db.backup()

        self._config.set("window_width", self.winfo_width())
        self._config.set("window_height", self.winfo_height())

        logger.info("Aplicacion cerrada")
        self.destroy()
