"""
PC Parts Tracker - Configuración de Base de Datos

Maneja la conexión SQLite, creación de tablas y sesiones.
"""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base
from utils.logger import get_logger

logger = get_logger("database")

DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "database.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"


class Database:
    """Gestor central de la base de datos."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        url = f"sqlite:///{self._db_path}"
        self._engine = create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(self._engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        logger.info("Base de datos inicializada: %s", self._db_path)

    def create_tables(self) -> None:
        """Crea todas las tablas definidas en los modelos."""
        Base.metadata.create_all(bind=self._engine)
        logger.info("Tablas creadas/verificadas")

    def get_session(self) -> Session:
        """Retorna una nueva sesión de base de datos."""
        return self._session_factory()

    def backup(self, backup_dir: Path | None = None) -> Path | None:
        """
        Crea una copia de seguridad de la base de datos.

        Args:
            backup_dir: Directorio destino. Si es None, usa data/backups/.

        Returns:
            Ruta del archivo de backup o None si falló.
        """
        import shutil
        from datetime import datetime

        target_dir = backup_dir or (self._db_path.parent / "backups")
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = target_dir / f"database_backup_{timestamp}.db"

        try:
            shutil.copy2(self._db_path, backup_path)
            logger.info("Backup creado: %s", backup_path)
            return backup_path
        except OSError as e:
            logger.error("Error creando backup: %s", e)
            return None

    @property
    def engine(self):
        return self._engine

    @property
    def db_path(self) -> Path:
        return self._db_path
