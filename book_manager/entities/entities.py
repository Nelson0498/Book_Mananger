"""
Entidades del sistema de gestión de inventario de la librería.

Cada clase representa una entidad del dominio, con encapsulación de
sus atributos mediante atributos privados (name mangling) y acceso
controlado a través de properties.
"""

import abc
from datetime import date
from typing import Optional


class EntidadBase(abc.ABC):
    """Clase base abstracta para entidades identificadas por un id numérico.

    Provee una propiedad `id` uniforme para que los repositorios genéricos
    (ver IRepositorio en repositories.py) puedan operar sobre cualquier
    entidad sin conocer el nombre específico de su identificador.
    """

    @property
    @abc.abstractmethod
    def id(self) -> int:
        ...


class Genero(EntidadBase):
    """Entidad que representa un género literario."""

    def __init__(self, id_genero: int, nombre: str):
        self.__id_genero = id_genero
        self.__nombre = nombre

    @property
    def id(self) -> int:
        return self.__id_genero

    @property
    def id_genero(self) -> int:
        return self.__id_genero

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not valor:
            raise ValueError("El nombre del género no puede estar vacío")
        self.__nombre = valor

    def __str__(self) -> str:
        return self.__nombre

    def __repr__(self) -> str:
        return f"Genero(id_genero={self.__id_genero}, nombre='{self.__nombre}')"


class Moneda(EntidadBase):
    """Entidad que representa una moneda en la que se puede expresar un precio."""

    def __init__(self, id_moneda: int, codigo: str, nombre: str, simbolo: str):
        self.__id_moneda = id_moneda
        self.__codigo = codigo.upper()
        self.__nombre = nombre
        self.__simbolo = simbolo

    @property
    def id(self) -> int:
        return self.__id_moneda

    @property
    def id_moneda(self) -> int:
        return self.__id_moneda

    @property
    def codigo(self) -> str:
        return self.__codigo

    @codigo.setter
    def codigo(self, valor: str) -> None:
        if not valor:
            raise ValueError("El código de la moneda no puede estar vacío")
        self.__codigo = valor.upper()

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        self.__nombre = valor

    @property
    def simbolo(self) -> str:
        return self.__simbolo

    @simbolo.setter
    def simbolo(self, valor: str) -> None:
        self.__simbolo = valor

    def __str__(self) -> str:
        return f"{self.__codigo} ({self.__simbolo})"

    def __repr__(self) -> str:
        return f"Moneda(id_moneda={self.__id_moneda}, codigo='{self.__codigo}')"


class TipoCotizacion(EntidadBase):
    """Entidad que representa un tipo de cotización del dólar (Oficial, Blue, MEP, etc.)."""

    def __init__(self, id_tipo: int, nombre: str):
        self.__id_tipo = id_tipo
        self.__nombre = nombre

    @property
    def id(self) -> int:
        return self.__id_tipo

    @property
    def id_tipo(self) -> int:
        return self.__id_tipo

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not valor:
            raise ValueError("El nombre del tipo de cotización no puede estar vacío")
        self.__nombre = valor

    def __str__(self) -> str:
        return self.__nombre

    def __repr__(self) -> str:
        return f"TipoCotizacion(id_tipo={self.__id_tipo}, nombre='{self.__nombre}')"


class Editorial(EntidadBase):
    """Entidad que representa la editorial/distribuidora que provee los libros."""

    def __init__(self, id_editorial: int, nombre: str, pais: Optional[str] = None):
        self.__id_editorial = id_editorial
        self.__nombre = nombre
        self.__pais = pais

    @property
    def id(self) -> int:
        return self.__id_editorial

    @property
    def id_editorial(self) -> int:
        return self.__id_editorial

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if not valor:
            raise ValueError("El nombre de la editorial no puede estar vacío")
        self.__nombre = valor

    @property
    def pais(self) -> Optional[str]:
        return self.__pais

    @pais.setter
    def pais(self, valor: Optional[str]) -> None:
        self.__pais = valor

    def __str__(self) -> str:
        return self.__nombre

    def __repr__(self) -> str:
        return f"Editorial(id_editorial={self.__id_editorial}, nombre='{self.__nombre}')"


class Precio(EntidadBase):
    """Entidad que representa el valor de un libro en una moneda específica."""

    def __init__(self, id_precio: int, valor: float, moneda: Moneda):
        self.__id_precio = id_precio
        self.valor = valor  # usa el setter para validar
        self.__moneda = moneda

    @property
    def id(self) -> int:
        return self.__id_precio

    @property
    def id_precio(self) -> int:
        return self.__id_precio

    @property
    def valor(self) -> float:
        return self.__valor

    @valor.setter
    def valor(self, nuevo_valor: float) -> None:
        if nuevo_valor < 0:
            raise ValueError("El precio no puede ser negativo")
        self.__valor = nuevo_valor

    @property
    def moneda(self) -> Moneda:
        return self.__moneda

    @moneda.setter
    def moneda(self, nueva_moneda: Moneda) -> None:
        self.__moneda = nueva_moneda

    def __str__(self) -> str:
        return f"{self.__valor:.2f} {self.__moneda.codigo}"

    def __repr__(self) -> str:
        return f"Precio(valor={self.__valor}, moneda={self.__moneda.codigo})"


class Stock(EntidadBase):
    """Entidad que representa la cantidad disponible de un libro."""

    def __init__(self, id_stock: int, cantidad: int, cantidad_minima: int = 0,
                 libro_isbn: Optional[str] = None):
        self.__id_stock = id_stock
        self.cantidad = cantidad  # usa el setter para validar
        self.__cantidad_minima = cantidad_minima
        self.__libro_isbn = libro_isbn

    @property
    def id(self) -> int:
        return self.__id_stock

    @property
    def id_stock(self) -> int:
        return self.__id_stock

    @property
    def libro_isbn(self) -> Optional[str]:
        """ISBN del libro al que pertenece este registro de stock (relación 1 a 1)."""
        return self.__libro_isbn

    @libro_isbn.setter
    def libro_isbn(self, valor: str) -> None:
        self.__libro_isbn = valor

    @property
    def cantidad(self) -> int:
        return self.__cantidad

    @cantidad.setter
    def cantidad(self, valor: int) -> None:
        if valor < 0:
            raise ValueError("La cantidad en stock no puede ser negativa")
        self.__cantidad = valor

    @property
    def cantidad_minima(self) -> int:
        return self.__cantidad_minima

    @cantidad_minima.setter
    def cantidad_minima(self, valor: int) -> None:
        self.__cantidad_minima = valor

    def hay_stock_bajo(self) -> bool:
        """Indica si la cantidad actual está por debajo del mínimo definido."""
        return self.__cantidad <= self.__cantidad_minima

    def __str__(self) -> str:
        return f"{self.__cantidad} unidades"

    def __repr__(self) -> str:
        return f"Stock(id_stock={self.__id_stock}, cantidad={self.__cantidad})"


class CotizacionDolar(EntidadBase):
    """Entidad que representa el registro histórico de la cotización del dólar."""

    def __init__(self, id_cotizacion: int, tipo: TipoCotizacion,
                 valor_compra: float, valor_venta: float,
                 fecha: Optional[date] = None):
        self.__id_cotizacion = id_cotizacion
        self.__tipo = tipo
        self.valor_compra = valor_compra
        self.valor_venta = valor_venta
        self.__fecha = fecha if fecha is not None else date.today()

    @property
    def id(self) -> int:
        return self.__id_cotizacion

    @property
    def id_cotizacion(self) -> int:
        return self.__id_cotizacion

    @property
    def tipo(self) -> TipoCotizacion:
        return self.__tipo

    @property
    def valor_compra(self) -> float:
        return self.__valor_compra

    @valor_compra.setter
    def valor_compra(self, valor: float) -> None:
        if valor < 0:
            raise ValueError("El valor de compra no puede ser negativo")
        self.__valor_compra = valor

    @property
    def valor_venta(self) -> float:
        return self.__valor_venta

    @valor_venta.setter
    def valor_venta(self, valor: float) -> None:
        if valor < 0:
            raise ValueError("El valor de venta no puede ser negativo")
        self.__valor_venta = valor

    @property
    def fecha(self) -> date:
        return self.__fecha

    def __str__(self) -> str:
        return f"{self.__tipo.nombre}: compra {self.__valor_compra} / venta {self.__valor_venta} ({self.__fecha})"

    def __repr__(self) -> str:
        return f"CotizacionDolar(tipo={self.__tipo.nombre}, fecha={self.__fecha})"


class Libro:
    """Entidad principal que representa un título del catálogo."""

    def __init__(self, isbn: str, titulo: str, autor: str,
                 editorial: Editorial, genero: Genero,
                 precio: Precio, stock: Stock):
        if not isbn:
            raise ValueError("El ISBN no puede estar vacío")
        if not titulo:
            raise ValueError("El título no puede estar vacío")

        self.__isbn = isbn
        self.__titulo = titulo
        self.__autor = autor
        self.__editorial = editorial
        self.__genero = genero
        self.__precio = precio
        self.__stock = stock

    @property
    def isbn(self) -> str:
        return self.__isbn

    @property
    def titulo(self) -> str:
        return self.__titulo

    @titulo.setter
    def titulo(self, valor: str) -> None:
        if not valor:
            raise ValueError("El título no puede estar vacío")
        self.__titulo = valor

    @property
    def autor(self) -> str:
        return self.__autor

    @autor.setter
    def autor(self, valor: str) -> None:
        self.__autor = valor

    @property
    def editorial(self) -> Editorial:
        return self.__editorial

    @editorial.setter
    def editorial(self, valor: Editorial) -> None:
        self.__editorial = valor

    @property
    def genero(self) -> Genero:
        return self.__genero

    @genero.setter
    def genero(self, valor: Genero) -> None:
        self.__genero = valor

    @property
    def precio(self) -> Precio:
        return self.__precio

    @precio.setter
    def precio(self, valor: Precio) -> None:
        self.__precio = valor

    @property
    def stock(self) -> Stock:
        return self.__stock

    @stock.setter
    def stock(self, valor: Stock) -> None:
        self.__stock = valor

    def __str__(self) -> str:
        return f"'{self.__titulo}' de {self.__autor} ({self.__editorial.nombre}) - {self.__precio}"

    def __repr__(self) -> str:
        return f"Libro(isbn='{self.__isbn}', titulo='{self.__titulo}')"