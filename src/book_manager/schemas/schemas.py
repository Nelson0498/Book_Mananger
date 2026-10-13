"""
Esquemas Pydantic para validación y estructuración de datos de entrada.

Estos modelos NO reemplazan las entidades POO del dominio.  Su función
es validar los datos que ingresan desde la consola (u otra fuente
externa) antes de pasarlos a los servicios.

Flujo:
    Usuario → console.py → Schema Pydantic (validación) → Service → Entidad POO

Las reglas de negocio (ej: no eliminar moneda en uso, stock insuficiente)
permanecen en los servicios.  Pydantic solo se encarga de validar
estructura, tipos y restricciones simples de los datos de entrada.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Genero
# ---------------------------------------------------------------------------

class GeneroInput(BaseModel):
    """Datos de entrada para crear un género."""
    id_genero: int = Field(gt=0, description="ID del género")
    nombre: str = Field(min_length=1, description="Nombre del género")


class GeneroUpdateInput(BaseModel):
    """Datos de entrada para actualizar un género."""
    id_genero: int = Field(gt=0, description="ID del género a modificar")
    nuevo_nombre: str = Field(
        min_length=1, description="Nuevo nombre del género"
    )


# ---------------------------------------------------------------------------
# Editorial
# ---------------------------------------------------------------------------

class EditorialInput(BaseModel):
    """Datos de entrada para crear una editorial."""
    id_editorial: int = Field(gt=0, description="ID de la editorial")
    nombre: str = Field(min_length=1, description="Nombre de la editorial")
    pais: Optional[str] = Field(
        default=None, description="País de origen"
    )


class EditorialUpdateInput(BaseModel):
    """Datos de entrada para actualizar una editorial."""
    id_editorial: int = Field(
        gt=0, description="ID de la editorial a modificar"
    )
    nombre: Optional[str] = Field(
        default=None, min_length=1, description="Nuevo nombre"
    )
    pais: Optional[str] = Field(
        default=None, description="Nuevo país"
    )


# ---------------------------------------------------------------------------
# Moneda
# ---------------------------------------------------------------------------

class MonedaInput(BaseModel):
    """Datos de entrada para crear una moneda."""
    id_moneda: int = Field(gt=0, description="ID de la moneda")
    codigo: str = Field(min_length=1, description="Código ISO (ej: USD)")
    nombre: str = Field(min_length=1, description="Nombre de la moneda")
    simbolo: str = Field(min_length=1, description="Símbolo (ej: US$)")


class MonedaUpdateInput(BaseModel):
    """Datos de entrada para actualizar una moneda."""
    id_moneda: int = Field(gt=0, description="ID de la moneda a modificar")
    nombre: Optional[str] = Field(
        default=None, min_length=1, description="Nuevo nombre"
    )
    simbolo: Optional[str] = Field(
        default=None, min_length=1, description="Nuevo símbolo"
    )


# ---------------------------------------------------------------------------
# TipoCotizacion
# ---------------------------------------------------------------------------

class TipoCotizacionInput(BaseModel):
    """Datos de entrada para crear un tipo de cotización."""
    id_tipo: int = Field(gt=0, description="ID del tipo")
    nombre: str = Field(
        min_length=1, description="Nombre del tipo de cotización"
    )


class TipoCotizacionUpdateInput(BaseModel):
    """Datos de entrada para actualizar un tipo de cotización."""
    id_tipo: int = Field(gt=0, description="ID del tipo a modificar")
    nuevo_nombre: str = Field(
        min_length=1, description="Nuevo nombre del tipo"
    )


# ---------------------------------------------------------------------------
# Precio
# ---------------------------------------------------------------------------

class PrecioInput(BaseModel):
    """Datos de entrada para crear un precio."""
    id_precio: int = Field(gt=0, description="ID del precio")
    valor: float = Field(ge=0, description="Valor del precio")
    moneda_id: int = Field(gt=0, description="ID de la moneda asociada")


class PrecioUpdateInput(BaseModel):
    """Datos de entrada para actualizar un precio."""
    id_precio: int = Field(gt=0, description="ID del precio a modificar")
    nuevo_valor: float = Field(ge=0, description="Nuevo valor del precio")


# ---------------------------------------------------------------------------
# Stock
# ---------------------------------------------------------------------------

class StockInput(BaseModel):
    """Datos de entrada para crear un stock."""
    id_stock: int = Field(gt=0, description="ID del stock")
    libro_isbn: str = Field(
        min_length=1, description="ISBN del libro asociado"
    )
    cantidad: int = Field(ge=0, description="Cantidad inicial")
    cantidad_minima: int = Field(ge=0, description="Cantidad mínima")


class StockMovimientoInput(BaseModel):
    """Datos de entrada para registrar un ingreso o egreso de stock."""
    libro_isbn: str = Field(
        min_length=1, description="ISBN del libro"
    )
    cantidad: int = Field(gt=0, description="Cantidad a mover")


# ---------------------------------------------------------------------------
# Libro
# ---------------------------------------------------------------------------

class LibroInput(BaseModel):
    """Datos de entrada para crear un libro con su precio y stock."""
    isbn: str = Field(min_length=1, description="ISBN del libro")
    titulo: str = Field(min_length=1, description="Título del libro")
    autor: str = Field(min_length=1, description="Autor del libro")
    editorial_id: int = Field(gt=0, description="ID de la editorial")
    genero_id: int = Field(gt=0, description="ID del género")
    precio_id: int = Field(gt=0, description="ID para el nuevo precio")
    precio_valor: float = Field(ge=0, description="Valor del precio")
    moneda_id: int = Field(gt=0, description="ID de la moneda")
    stock_id: int = Field(gt=0, description="ID para el stock")
    cantidad_inicial: int = Field(ge=0, description="Cantidad inicial")
    cantidad_minima: int = Field(ge=0, description="Cantidad mínima")


class LibroUpdateInput(BaseModel):
    """Datos de entrada para actualizar datos de un libro."""
    isbn: str = Field(min_length=1, description="ISBN del libro a modificar")
    titulo: Optional[str] = Field(
        default=None, min_length=1, description="Nuevo título"
    )
    autor: Optional[str] = Field(
        default=None, min_length=1, description="Nuevo autor"
    )


class LibroPrecioUpdateInput(BaseModel):
    """Datos de entrada para actualizar el precio de un libro."""
    isbn: str = Field(min_length=1, description="ISBN del libro")
    nuevo_valor: float = Field(
        ge=0, description="Nuevo valor del precio"
    )


# ---------------------------------------------------------------------------
# CotizacionDolar
# ---------------------------------------------------------------------------

class CotizacionDolarInput(BaseModel):
    """Datos de entrada para registrar una cotización del dólar."""
    id_cotizacion: int = Field(gt=0, description="ID de la cotización")
    tipo_id: int = Field(gt=0, description="ID del tipo de cotización")
    valor_compra: float = Field(
        ge=0, description="Valor de compra"
    )
    valor_venta: float = Field(
        ge=0, description="Valor de venta"
    )
    fecha: date = Field(description="Fecha de la cotización (AAAA-MM-DD)")

    @field_validator('valor_venta')
    @classmethod
    def compra_no_mayor_que_venta(
        cls, valor_venta: float, info
    ) -> float:
        """Valida que el valor de compra no sea mayor al de venta."""
        valor_compra = info.data.get('valor_compra')
        if valor_compra is not None and valor_compra > valor_venta:
            raise ValueError(
                'El valor de compra no puede ser mayor al de venta'
            )
        return valor_venta


class CotizacionDolarUpdateInput(BaseModel):
    """Datos de entrada para actualizar una cotización."""
    tipo_id: int = Field(gt=0, description="ID del tipo")
    fecha: date = Field(description="Fecha de la cotización")
    nuevo_valor_compra: float = Field(
        ge=0, description="Nuevo valor de compra"
    )
    nuevo_valor_venta: float = Field(
        ge=0, description="Nuevo valor de venta"
    )

    @field_validator('nuevo_valor_venta')
    @classmethod
    def compra_no_mayor_que_venta(
        cls, nuevo_valor_venta: float, info
    ) -> float:
        """Valida que el valor de compra no sea mayor al de venta."""
        compra = info.data.get('nuevo_valor_compra')
        if compra is not None and compra > nuevo_valor_venta:
            raise ValueError(
                'El valor de compra no puede ser mayor al de venta'
            )
        return nuevo_valor_venta
