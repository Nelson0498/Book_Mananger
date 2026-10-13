"""
Modelos ORM del sistema de gestión de inventario de la librería.

Cada clase representa una tabla de la base de datos y declara sus tipos de
datos, restricciones y relaciones. Los nombres de las tablas y de las columnas
coinciden con los encabezados de los archivos CSV del Sprint 1, de modo que la
migración de datos sea una correspondencia directa y verificable.

Los identificadores son suministrados por la aplicación, igual que en el
Sprint 1, por lo que las claves primarias no dependen de secuencias
autogeneradas: la migración puede re-ejecutarse sin colisiones de secuencia.

Estas clases son el modelo de persistencia y no reemplazan a las entidades de
dominio de `entities/entities.py`, que conservan su encapsulamiento. La
conversión entre ambos mundos se realiza en los repositorios.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Clase base declarativa de la que heredan todos los modelos.

    Las claves primarias se declaran con ``autoincrement=False`` de forma
    deliberada: los identificadores siempre los provee la aplicación, así que
    no se generan secuencias que puedan quedar desincronizadas respecto de los
    ids ya migrados desde los CSV.
    """


class GeneroModel(Base):
    """Tabla `generos`: géneros literarios del catálogo."""

    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    nombre: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )

    libros: Mapped[List["LibroModel"]] = relationship(back_populates="genero")

    def __repr__(self) -> str:
        return f"GeneroModel(id={self.id}, nombre='{self.nombre}')"


class EditorialModel(Base):
    """Tabla `editoriales`: editoriales o distribuidoras que proveen libros."""

    __tablename__ = "editoriales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    pais: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    libros: Mapped[List["LibroModel"]] = relationship(
        back_populates="editorial"
    )

    def __repr__(self) -> str:
        return f"EditorialModel(id={self.id}, nombre='{self.nombre}')"


class MonedaModel(Base):
    """Tabla `monedas`: monedas en las que puede expresarse un precio."""

    __tablename__ = "monedas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    codigo: Mapped[str] = mapped_column(
        String(10), nullable=False, unique=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    simbolo: Mapped[str] = mapped_column(String(10), nullable=False)

    precios: Mapped[List["PrecioModel"]] = relationship(
        back_populates="moneda"
    )

    def __repr__(self) -> str:
        return f"MonedaModel(id={self.id}, codigo='{self.codigo}')"


class TipoCotizacionModel(Base):
    """Tabla `tipos_cotizacion`: tipos de cotización del dólar."""

    __tablename__ = "tipos_cotizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    nombre: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )

    cotizaciones: Mapped[List["CotizacionDolarModel"]] = relationship(
        back_populates="tipo"
    )

    def __repr__(self) -> str:
        return f"TipoCotizacionModel(id={self.id}, nombre='{self.nombre}')"


class PrecioModel(Base):
    """Tabla `precios`: valor de un libro en una moneda determinada."""

    __tablename__ = "precios"
    __table_args__ = (
        CheckConstraint(
            "valor >= 0", name="ck_precios_valor_no_negativo"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    moneda_id: Mapped[int] = mapped_column(
        ForeignKey("monedas.id"), nullable=False, index=True
    )

    moneda: Mapped["MonedaModel"] = relationship(back_populates="precios")
    # `passive_deletes` evita que el ORM intente anular libros.precio_id (que es
    # NOT NULL) al borrar un precio: la integridad la controla la base de datos.
    libro: Mapped[Optional["LibroModel"]] = relationship(
        back_populates="precio", uselist=False, passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"PrecioModel(id={self.id}, valor={self.valor})"


class LibroModel(Base):
    """Tabla `libros`: catálogo de títulos.

    El ISBN es la clave primaria natural. La relación con `precios` es uno a
    uno, garantizada por la restricción de unicidad sobre `precio_id`.
    """

    __tablename__ = "libros"
    __table_args__ = (
        UniqueConstraint("precio_id", name="uq_libros_precio"),
    )

    isbn: Mapped[str] = mapped_column(String(20), primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    autor: Mapped[str] = mapped_column(String(150), nullable=False)
    editorial_id: Mapped[int] = mapped_column(
        ForeignKey("editoriales.id"), nullable=False, index=True
    )
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos.id"), nullable=False, index=True
    )
    precio_id: Mapped[int] = mapped_column(
        ForeignKey("precios.id"), nullable=False
    )

    editorial: Mapped["EditorialModel"] = relationship(
        back_populates="libros"
    )
    genero: Mapped["GeneroModel"] = relationship(back_populates="libros")
    precio: Mapped["PrecioModel"] = relationship(back_populates="libro")
    stock: Mapped[Optional["StockModel"]] = relationship(
        back_populates="libro", uselist=False
    )

    def __repr__(self) -> str:
        return f"LibroModel(isbn='{self.isbn}', titulo='{self.titulo}')"


class StockModel(Base):
    """Tabla `stock`: cantidad disponible de cada libro (uno a uno por ISBN)."""

    __tablename__ = "stock"
    __table_args__ = (
        UniqueConstraint("libro_isbn", name="uq_stock_libro"),
        CheckConstraint(
            "cantidad >= 0", name="ck_stock_cantidad_no_negativa"
        ),
    )

    id_stock: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    libro_isbn: Mapped[str] = mapped_column(
        ForeignKey("libros.isbn"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_minima: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    libro: Mapped["LibroModel"] = relationship(back_populates="stock")

    def __repr__(self) -> str:
        return (
            f"StockModel(id_stock={self.id_stock}, "
            f"cantidad={self.cantidad})"
        )


class CotizacionDolarModel(Base):
    """Tabla `cotizaciones`: registro histórico de la cotización del dólar.

    La restricción de unicidad sobre `(tipo_id, fecha)` evita duplicados al
    consultar la API más de una vez para el mismo día.
    """

    __tablename__ = "cotizaciones"
    __table_args__ = (
        UniqueConstraint(
            "tipo_id", "fecha", name="uq_cotizaciones_tipo_fecha"
        ),
        CheckConstraint(
            "valor_compra <= valor_venta",
            name="ck_cotizaciones_compra_venta",
        ),
    )

    id_cotizacion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    tipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_cotizacion.id"), nullable=False, index=True
    )
    valor_compra: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    valor_venta: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)

    tipo: Mapped["TipoCotizacionModel"] = relationship(
        back_populates="cotizaciones"
    )

    def __repr__(self) -> str:
        return (
            f"CotizacionDolarModel(id_cotizacion={self.id_cotizacion}, "
            f"fecha={self.fecha})"
        )
