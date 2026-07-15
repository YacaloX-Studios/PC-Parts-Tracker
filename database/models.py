"""
PC Parts Tracker - Modelos ORM

Define las tablas de la base de datos usando SQLAlchemy 2.0
con type hints y Mapped[T].
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pcbuilding_core.enums import ComponentCategory, Currency
from pcbuilding_core.models import Component, PriceRecord, Build as CoreBuild


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""
    pass


class Product(Base):
    """Modelo de producto/componente de PC."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Sin categoria")
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    store: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    lowest_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    highest_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="COP")
    target_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    build_items: Mapped[list["BuildItem"]] = relationship(
        back_populates="product"
    )

    def __repr__(self) -> str:
        return (
            f"<Product(id={self.id}, name='{self.name}', "
            f"price={self.current_price}, store='{self.store}')>"
        )

    @property
    def price_change_pct(self) -> float | None:
        """Calcula el cambio porcentual respecto al precio anterior."""
        if self.current_price and self.previous_price and self.previous_price > 0:
            return ((self.current_price - self.previous_price) / self.previous_price) * 100
        return None

    @property
    def display_name(self) -> str:
        """Nombre formateado para la GUI."""
        brand_part = f"{self.brand} " if self.brand else ""
        model_part = f"{self.model}" if self.model else self.name
        return f"{brand_part}{model_part}"

    @property
    def category_enum(self) -> ComponentCategory:
        """Categoría como enum de pcbuilding-core."""
        return ComponentCategory.from_string(self.category)

    @property
    def currency_enum(self) -> Currency:
        """Moneda como enum de pcbuilding-core."""
        return Currency.from_string(self.currency)

    def to_component(self) -> Component:
        """Convierte este ORM Product a un Component dataclass de pcbuilding-core."""
        return Component(
            name=self.name,
            category=self.category_enum,
            brand=self.brand or "",
            model=self.model or "",
            price=self.current_price,
            currency=self.currency_enum,
            url=self.url,
            store=self.store,
            target_price=self.target_price,
            created_at=self.created_at,
            id=self.id,
        )


class PriceHistory(Base):
    """Historial de precios de un producto."""

    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    product: Mapped["Product"] = relationship(back_populates="price_history")

    def __repr__(self) -> str:
        return (
            f"<PriceHistory(product_id={self.product_id}, "
            f"price={self.price}, date='{self.date}')>"
        )

    def to_price_record(self) -> PriceRecord:
        """Convierte este ORM PriceHistory a un PriceRecord dataclass."""
        return PriceRecord(
            component_id=self.product_id,
            price=self.price,
            currency="COP",
            date=self.date,
            id=self.id,
        )


class Build(Base):
    """Una configuración/PC completa (build)."""

    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    items: Mapped[list["BuildItem"]] = relationship(
        back_populates="build", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Build(id={self.id}, name='{self.name}')>"

    def to_core_build(self, session) -> CoreBuild:
        """Convierte este ORM Build a un Build dataclass de pcbuilding-core.

        Necesita la sesión SQLAlchemy para resolver Product de cada BuildItem.
        """
        components = []
        for item in self.items:
            product = session.get(Product, item.product_id)
            if product:
                components.append(product.to_component())
        return CoreBuild(
            name=self.name,
            components=components,
            created_at=self.created_at,
            id=self.id,
        )


class BuildItem(Base):
    """Producto asociado a un build."""

    __tablename__ = "build_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    build_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("builds.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )

    build: Mapped["Build"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="build_items")

    def __repr__(self) -> str:
        return (
            f"<BuildItem(build_id={self.build_id}, product_id={self.product_id})>"
        )
