"""
PC Parts Tracker - Punto de Entrada

Inicializa la base de datos, detecta si hay Excel existente
para migrar, y lanza la ventana principal.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.database import Database
from database.models import Product
from utils.config import AppConfig
from utils.logger import setup_logger, get_logger
from utils.excel import ExcelManager
from repositories.product_repository import ProductRepository


EXCEL_PATH = project_root / "Cotización PC Gamer.xlsm"


def check_first_run(db: Database, config: AppConfig) -> None:
    """
    Verifica si es el primer inicio de la aplicación.
    Si no existe la DB y hay un Excel existente, ofrece migrarlo.
    """
    session = db.get_session()
    product_repo = ProductRepository(session)
    count = product_repo.count(active_only=False)

    if count > 0:
        return

    if not EXCEL_PATH.exists():
        return

    try:
        import customtkinter as ctk
        from tkinter import messagebox

        ctk.set_appearance_mode(config.appearance_mode)
        root = ctk.CTk()
        root.withdraw()

        response = messagebox.askyesno(
            "Bienvenido a PC Parts Tracker",
            "Es tu primera vez usando PC Parts Tracker.\n\n"
            f"Se encontro el archivo:\n{EXCEL_PATH.name}\n\n"
            "Se encontraron productos en la hoja de calculo.\n"
            "¿Deseas importarlos automaticamente?",
        )

        if response:
            excel_mgr = ExcelManager()
            products_data = excel_mgr.migrate_from_existing_excel(str(EXCEL_PATH))

            imported = 0
            for data in products_data:
                product = Product(
                    name=data["name"],
                    category=data["category"],
                    brand=data["brand"],
                    model=data["model"],
                    store=data["store"],
                    url=data["url"],
                    current_price=data["current_price"],
                    previous_price=data["previous_price"],
                    lowest_price=data["lowest_price"],
                    highest_price=data["highest_price"],
                    currency=data["currency"],
                    target_price=data["target_price"],
                    active=data["active"],
                )
                session.add(product)
                imported += 1

            session.commit()

            from repositories.history_repository import HistoryRepository
            history_repo = HistoryRepository(session)

            for data in products_data:
                if data["current_price"]:
                    stmt = session.query(Product).filter(
                        Product.name == data["name"]
                    ).first()
                    if stmt:
                        history_repo.add_record(stmt.id, data["current_price"])

            messagebox.showinfo(
                "Importacion completada",
                f"Se importaron {imported} productos correctamente.\n\n"
                "Ya puedes usar PC Parts Tracker.",
            )

        root.destroy()

    except Exception as e:
        logger = get_logger("main")
        logger.error("Error durante la migracion inicial: %s", e)


def main() -> None:
    """Funcion principal de la aplicacion."""
    config = AppConfig()
    logger = setup_logger(developer_mode=config.developer_mode)
    logger.info("=" * 60)
    logger.info("PC Parts Tracker iniciando...")
    logger.info("=" * 60)

    db = Database()
    db.create_tables()

    check_first_run(db, config)

    from gui.main_window import MainWindow

    app = MainWindow(config=config, db=db)
    app.mainloop()

    logger.info("PC Parts Tracker finalizado")


if __name__ == "__main__":
    main()
