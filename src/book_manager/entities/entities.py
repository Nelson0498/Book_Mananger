"""Entidades del sistema de gestión de inventario de la librería.

Cada clase representa una entidad del dominio, con encapsulación de
sus atributos mediante atributos privados (name mangling) y acceso
controlado a través de properties.

Las relaciones entre entidades se expresan por objeto y no por
identificador: un `Precio` y un `Stock` conocen al `Libro` al que
pertenecen, y el `Libro` conoce sus precios (uno por moneda) y su stock.
"""

import abc
from datetime import date, datetime
from typing import List, Optional


class EntidadBase(abc.ABC):
    """Clase base abstracta para entidades identificadas por un id numérico.

    Provee una propiedad `id` uniforme para que los repositorios genéricos
    (ver IRepositorio en repositories.py) puedan operar sobre cualquier
    entidad sin conocer el nombre específico de su identificador.
    """

    @property
    @abc.abstractmethod
    def id(self) -> int:
        """Identificador numérico de la entidad."""


class Genero(EntidadBase):
    """Entidad que representa un género literario."""

    def __init__(self, id_genero: int, nombre: str) -> None:
        """Crea un género.

        Args:
            id_genero (int): Identificador del género.
            nombre (str): Nombre del género.
        """
        self.__id_genero = id_genero
        self.__nombre = nombre

    @property
    def id(self) -> int:
        """Identificador numérico de la entidad."""
        return self.__id_genero

    @property
    def id_genero(self) -> int:
        """Identificador del género."""
        return self.__id_genero

    @property
    def nombre(self) -> str:
        """Nombre del género."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Modifica el nombre del género.

        Raises:
            ValueError: Si el nombre está vacío.
        """
        if not valor:
            raise ValueError("El nombre del género no puede estar vacío")
        self.__nombre = valor

    def __str__(self) -> str:
        """Devuelve el nombre del género."""
        return self.__nombre

    def __repr__(self) -> str:
        """Devuelve una representación técnica del género."""
        return (
            f"Genero(id_genero={self.__id_genero}, "
            f"nombre='{self.__nombre}')"
        )


class Moneda(EntidadBase):
    """Entidad que representa una moneda en la que se expresa un precio."""

    def __init__(self, id_moneda: int, codigo: str, nombre: str,
                 simbolo: str) -> None:
        """Crea una moneda.

        Args:
            id_moneda (int): Identificador de la moneda.
            codigo (str): Código de la moneda (por ejemplo, USD).
            nombre (str): Nombre de la moneda.
            simbolo (str): Símbolo de la moneda (por ejemplo, US$).
        """
        self.__id_moneda = id_moneda
        self.__codigo = codigo.upper()
        self.__nombre = nombre
        self.__simbolo = simbolo

    @property
    def id(self) -> int:
        """Identificador numérico de la entidad."""
        return self.__id_moneda

    @property
    def id_moneda(self) -> int:
        """Identificador de la moneda."""
        return self.__id_moneda

    @property
    def codigo(self) -> str:
        """Código de la moneda, siempre en mayúsculas."""
        return self.__codigo

    @codigo.setter
    def codigo(self, valor: str) -> None:
        """Modifica el código de la moneda.

        Raises:
            ValueError: Si el código está vacío.
        """
        if not valor:
            raise ValueError("El código de la moneda no puede estar vacío")
        self.__codigo = valor.upper()

    @property
    def nombre(self) -> str:
        """Nombre de la moneda."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Modifica el nombre de la moneda.

        Se rechazan la cadena vacía y las formadas solo por espacios.

        Raises:
            ValueError: Si el nombre está vacío.
        """
        if not valor or not valor.strip():
            raise ValueError("El nombre de la moneda no puede estar vacío")
        self.__nombre = valor

    @property
    def simbolo(self) -> str:
        """Símbolo de la moneda."""
        return self.__simbolo

    @simbolo.setter
    def simbolo(self, valor: str) -> None:
        """Modifica el símbolo de la moneda.

        Se rechazan la cadena vacía y las formadas solo por espacios.

        Raises:
            ValueError: Si el símbolo está vacío.
        """
        if not valor or not valor.strip():
            raise ValueError("El símbolo de la moneda no puede estar vacío")
        self.__simbolo = valor

    def __str__(self) -> str:
        """Devuelve el código y el símbolo de la moneda."""
        return f"{self.__codigo} ({self.__simbolo})"

    def __repr__(self) -> str:
        """Devuelve una representación técnica de la moneda."""
        return (
            f"Moneda(id_moneda={self.__id_moneda}, "
            f"codigo='{self.__codigo}')"
        )


class TipoCotizacion(EntidadBase):
    """Entidad que representa un tipo de cotización (Oficial, Blue, etc.)."""

    def __init__(self, id_tipo: int, nombre: str) -> None:
        """Crea un tipo de cotización.

        Args:
            id_tipo (int): Identificador del tipo.
            nombre (str): Nombre del tipo.
        """
        self.__id_tipo = id_tipo
        self.__nombre = nombre

    @property
    def id(self) -> int:
        """Identificador numérico de la entidad."""
        return self.__id_tipo

    @property
    def id_tipo(self) -> int:
        """Identificador del tipo de cotización."""
        return self.__id_tipo

    @property
    def nombre(self) -> str:
        """Nombre del tipo de cotización."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Modifica el nombre del tipo de cotización.

        Raises:
            ValueError: Si el nombre está vacío.
        """
        if not valor:
            raise ValueError(
                "El nombre del tipo de cotización no puede estar vacío"
            )
        self.__nombre = valor

    def __str__(self) -> str:
        """Devuelve el nombre del tipo."""
        return self.__nombre

    def __repr__(self) -> str:
        """Devuelve una representación técnica del tipo."""
        return (
            f"TipoCotizacion(id_tipo={self.__id_tipo}, "
            f"nombre='{self.__nombre}')"
        )


class Editorial(EntidadBase):
    """Entidad que representa la editorial que provee los libros."""

    def __init__(self, id_editorial: int, nombre: str,
                 pais: Optional[str] = None) -> None:
        """Crea una editorial.

        Args:
            id_editorial (int): Identificador de la editorial.
            nombre (str): Nombre de la editorial.
            pais (Optional[str]): País de origen.
        """
        self.__id_editorial = id_editorial
        self.__nombre = nombre
        self.__pais = pais

    @property
    def id(self) -> int:
        """Identificador numérico de la entidad."""
        return self.__id_editorial

    @property
    def id_editorial(self) -> int:
        """Identificador de la editorial."""
        return self.__id_editorial

    @property
    def nombre(self) -> str:
        """Nombre de la editorial."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Modifica el nombre de la editorial.

        Raises:
            ValueError: Si el nombre está vacío.
        """
        if not valor:
            raise ValueError("El nombre de la editorial no puede estar vacío")
        self.__nombre = valor

    @property
    def pais(self) -> Optional[str]:
        """País de origen de la editorial."""
        return self.__pais

    @pais.setter
    def pais(self, valor: Optional[str]) -> None:
        """Modifica el país de la editorial."""
        self.__pais = valor

    def __str__(self) -> str:
        """Devuelve el nombre de la editorial."""
        return self.__nombre

    def __repr__(self) -> str:
        """Devuelve una representación técnica de la editorial."""
        return (
            f"Editorial(id_editorial={self.__id_editorial}, "
            f"nombre='{self.__nombre}')"
        )


class Precio(EntidadBase):
    """Entidad que representa el valor de un libro en una moneda."""

    def __init__(self, id_precio: int, valor: float, moneda: Moneda,
                 libro: Optional["Libro"] = None) -> None:
        """Crea un precio.

        Args:
            id_precio (int): Identificador del precio.
            valor (float): Importe, no negativo.
            moneda (Moneda): Moneda en la que está expresado.
            libro (Optional[Libro]): Libro al que pertenece el precio.

        Raises:
            ValueError: Si el valor es negativo o la moneda no es válida.
        """
        self.__id_precio = id_precio
        self.valor = valor  # usa el setter para validar
        self.moneda = moneda  # usa el setter para validar
        self.__libro: Optional["Libro"] = None
        if libro is not None:
            self.libro = libro

    @property
    def id(self) -> int:
        """Identificador numérico de la entidad."""
        return self.__id_precio

    @property
    def id_precio(self) -> int:
        """Identificador del precio."""
        return self.__id_precio

    @property
    def valor(self) -> float:
        """Importe del precio."""
        return self.__valor

    @valor.setter
    def valor(self, nuevo_valor: float) -> None:
        """Modifica el importe del precio.

        Raises:
            ValueError: Si el importe es negativo.
        """
        if nuevo_valor < 0:
            raise ValueError("El precio no puede ser negativo")
        self.__valor = nuevo_valor

    @property
    def moneda(self) -> Moneda:
        """Moneda en la que está expresado el precio."""
        return self.__moneda

    @moneda.setter
    def moneda(self, nueva_moneda: Moneda) -> None:
        """Modifica la moneda del precio.

        Raises:
            ValueError: Si no es una instancia de Moneda.
        """
        if not isinstance(nueva_moneda, Moneda):
            raise ValueError(
                "La moneda del precio debe ser una instancia de Moneda"
            )
        self.__moneda = nueva_moneda

    @property
    def libro(self) -> Optional["Libro"]:
        """Libro al que pertenece el precio (None si aún no se asignó)."""
        return self.__libro

    @libro.setter
    def libro(self, valor: Optional["Libro"]) -> None:
        """Asigna el libro al que pertenece el precio.

        Raises:
            ValueError: Si no es un Libro ni None.
        """
        if valor is not None and not isinstance(valor, Libro):
            raise ValueError("El libro del precio debe ser una instancia "
                             "de Libro")
        self.__libro = valor

    def __str__(self) -> str:
        """Devuelve el importe seguido del código de moneda."""
        return f"{self.__valor:.2f} {self.__moneda.codigo}"

    def __repr__(self) -> str:
        """Devuelve una representación técnica del precio."""
        return (
            f"Precio(id_precio={self.__id_precio}, valor={self.__valor}, "
            f"moneda={self.__moneda.codigo})"
        )


class Stock(EntidadBase):
    """Entidad que representa la cantidad disponible de un libro."""

    def __init__(self, id_stock: int, cantidad: int,
                 cantidad_minima: int = 0,
                 libro: Optional["Libro"] = None) -> None:
        """Crea un registro de stock.

        Args:
            id_stock (int): Identificador del stock.
            cantidad (int): Unidades disponibles, no negativa.
            cantidad_minima (int): Umbral de reposición, no negativo.
            libro (Optional[Libro]): Libro al que pertenece el stock.

        Raises:
            ValueError: Si alguna cantidad es negativa.
        """
        self.__id_stock = id_stock
        self.cantidad = cantidad  # usa el setter para validar
        self.cantidad_minima = cantidad_minima  # usa el setter para validar
        self.__libro: Optional["Libro"] = None
        if libro is not None:
            self.libro = libro

    @property
    def id(self) -> int:
        """Identificador numérico de la entidad."""
        return self.__id_stock

    @property
    def id_stock(self) -> int:
        """Identificador del stock."""
        return self.__id_stock

    @property
    def libro(self) -> Optional["Libro"]:
        """Libro al que pertenece el stock (relación 1 a 1)."""
        return self.__libro

    @libro.setter
    def libro(self, valor: Optional["Libro"]) -> None:
        """Asigna el libro al que pertenece el stock.

        Raises:
            ValueError: Si no es un Libro ni None.
        """
        if valor is not None and not isinstance(valor, Libro):
            raise ValueError("El libro del stock debe ser una instancia "
                             "de Libro")
        self.__libro = valor

    @property
    def cantidad(self) -> int:
        """Unidades disponibles."""
        return self.__cantidad

    @cantidad.setter
    def cantidad(self, valor: int) -> None:
        """Modifica las unidades disponibles.

        Raises:
            ValueError: Si la cantidad es negativa.
        """
        if valor < 0:
            raise ValueError("La cantidad en stock no puede ser negativa")
        self.__cantidad = valor

    @property
    def cantidad_minima(self) -> int:
        """Umbral de reposición."""
        return self.__cantidad_minima

    @cantidad_minima.setter
    def cantidad_minima(self, valor: int) -> None:
        """Modifica el umbral de reposición.

        Raises:
            ValueError: Si el mínimo es negativo.
        """
        if valor < 0:
            raise ValueError("La cantidad mínima no puede ser negativa")
        self.__cantidad_minima = valor

    def hay_stock_bajo(self) -> bool:
        """Indica si la cantidad actual no supera el mínimo definido.

        Returns:
            bool: True si la cantidad es menor o igual al mínimo.
        """
        return self.__cantidad <= self.__cantidad_minima

    def __str__(self) -> str:
        """Devuelve la cantidad disponible."""
        return f"{self.__cantidad} unidades"

    def __repr__(self) -> str:
        """Devuelve una representación técnica del stock."""
        return (
            f"Stock(id_stock={self.__id_stock}, cantidad={self.__cantidad})"
        )


class CotizacionDolar(EntidadBase):
    """Entidad que representa el registro histórico del dólar."""

    def __init__(self, id_cotizacion: int, tipo: TipoCotizacion,
                 valor_compra: float, valor_venta: float,
                 fecha: Optional[date] = None) -> None:
        """Crea una cotización.

        Args:
            id_cotizacion (int): Identificador de la cotización.
            tipo (TipoCotizacion): Tipo de cotización.
            valor_compra (float): Valor de compra, no negativo.
            valor_venta (float): Valor de venta, no negativo.
            fecha (Optional[date]): Fecha; por defecto, la de hoy.

        Raises:
            ValueError: Si algún valor es negativo.
        """
        self.__id_cotizacion = id_cotizacion
        self.__tipo = tipo
        self.valor_compra = valor_compra
        self.valor_venta = valor_venta
        self.__fecha = fecha if fecha is not None else date.today()

    @property
    def id(self) -> int:
        """Identificador numérico de la entidad."""
        return self.__id_cotizacion

    @property
    def id_cotizacion(self) -> int:
        """Identificador de la cotización."""
        return self.__id_cotizacion

    @property
    def tipo(self) -> TipoCotizacion:
        """Tipo de cotización."""
        return self.__tipo

    @property
    def valor_compra(self) -> float:
        """Valor de compra."""
        return self.__valor_compra

    @valor_compra.setter
    def valor_compra(self, valor: float) -> None:
        """Modifica el valor de compra.

        Raises:
            ValueError: Si el valor es negativo.
        """
        if valor < 0:
            raise ValueError("El valor de compra no puede ser negativo")
        self.__valor_compra = valor

    @property
    def valor_venta(self) -> float:
        """Valor de venta."""
        return self.__valor_venta

    @valor_venta.setter
    def valor_venta(self, valor: float) -> None:
        """Modifica el valor de venta.

        Raises:
            ValueError: Si el valor es negativo.
        """
        if valor < 0:
            raise ValueError("El valor de venta no puede ser negativo")
        self.__valor_venta = valor

    @property
    def fecha(self) -> date:
        """Fecha de la cotización."""
        return self.__fecha

    def __str__(self) -> str:
        """Devuelve el tipo, los valores y la fecha."""
        return (
            f"{self.__tipo.nombre}: compra {self.__valor_compra} / "
            f"venta {self.__valor_venta} ({self.__fecha})"
        )

    def __repr__(self) -> str:
        """Devuelve una representación técnica de la cotización."""
        return (
            f"CotizacionDolar(tipo={self.__tipo.nombre}, "
            f"fecha={self.__fecha})"
        )


class Libro(EntidadBase):
    """Entidad principal que representa un título del catálogo.

    Un libro tiene un precio por moneda (relación 1 a N con `Precio`) y un
    único registro de stock (relación 1 a 1 con `Stock`).
    """

    def __init__(self, id_libro: int, isbn: str, titulo: str, autor: str,
                 editorial: Editorial, genero: Genero,
                 precios: Optional[List[Precio]] = None,
                 stock: Optional[Stock] = None) -> None:
        """Crea un libro.

        Args:
            id_libro (int): Identificador del libro, mayor que cero.
            isbn (str): ISBN del libro.
            titulo (str): Título del libro.
            autor (str): Autor del libro.
            editorial (Editorial): Editorial del libro.
            genero (Genero): Género del libro.
            precios (Optional[List[Precio]]): Precios, uno por moneda.
            stock (Optional[Stock]): Stock del libro.

        Raises:
            ValueError: Si algún dato es inválido o dos precios comparten
                moneda.
        """
        if id_libro <= 0:
            raise ValueError("El id del libro debe ser mayor que cero")

        self.__id_libro = id_libro
        self.isbn = isbn  # usa el setter para validar
        self.titulo = titulo  # usa el setter para validar
        self.__autor = autor
        self.__editorial = editorial
        self.__genero = genero
        self.__precios: List[Precio] = []
        self.__stock: Optional[Stock] = None

        for precio in precios or []:
            self.agregar_precio(precio)
        if stock is not None:
            self.stock = stock

    @property
    def id(self) -> int:
        """Identificador numérico de la entidad."""
        return self.__id_libro

    @property
    def id_libro(self) -> int:
        """Identificador del libro."""
        return self.__id_libro

    @property
    def isbn(self) -> str:
        """ISBN del libro."""
        return self.__isbn

    @isbn.setter
    def isbn(self, valor: str) -> None:
        """Modifica el ISBN del libro.

        Raises:
            ValueError: Si el ISBN está vacío.
        """
        if not valor or not valor.strip():
            raise ValueError("El ISBN no puede estar vacío")
        self.__isbn = valor

    @property
    def titulo(self) -> str:
        """Título del libro."""
        return self.__titulo

    @titulo.setter
    def titulo(self, valor: str) -> None:
        """Modifica el título del libro.

        Raises:
            ValueError: Si el título está vacío.
        """
        if not valor:
            raise ValueError("El título no puede estar vacío")
        self.__titulo = valor

    @property
    def autor(self) -> str:
        """Autor del libro."""
        return self.__autor

    @autor.setter
    def autor(self, valor: str) -> None:
        """Modifica el autor del libro.

        Se rechazan la cadena vacía y las formadas solo por espacios.

        Raises:
            ValueError: Si el autor está vacío.
        """
        if not valor or not valor.strip():
            raise ValueError("El autor no puede estar vacío")
        self.__autor = valor

    @property
    def editorial(self) -> Editorial:
        """Editorial del libro."""
        return self.__editorial

    @editorial.setter
    def editorial(self, valor: Editorial) -> None:
        """Modifica la editorial del libro.

        Raises:
            ValueError: Si no es una instancia de Editorial.
        """
        if not isinstance(valor, Editorial):
            raise ValueError(
                "La editorial debe ser una instancia de Editorial"
            )
        self.__editorial = valor

    @property
    def genero(self) -> Genero:
        """Género del libro."""
        return self.__genero

    @genero.setter
    def genero(self, valor: Genero) -> None:
        """Modifica el género del libro.

        Raises:
            ValueError: Si no es una instancia de Genero.
        """
        if not isinstance(valor, Genero):
            raise ValueError("El género debe ser una instancia de Genero")
        self.__genero = valor

    @property
    def precios(self) -> List[Precio]:
        """Copia de la lista de precios del libro (uno por moneda)."""
        return list(self.__precios)

    def agregar_precio(self, precio: Precio) -> None:
        """Agrega un precio al libro y le asigna la referencia al libro.

        Args:
            precio (Precio): Precio a agregar.

        Raises:
            ValueError: Si no es un Precio o ya existe uno en esa moneda.
        """
        if not isinstance(precio, Precio):
            raise ValueError("El precio debe ser una instancia de Precio")
        if self.precio_en(precio.moneda.codigo) is not None:
            raise ValueError(
                f"El libro ya tiene un precio en {precio.moneda.codigo}"
            )
        precio.libro = self
        self.__precios.append(precio)

    def quitar_precio(self, precio: Precio) -> None:
        """Quita un precio del libro y limpia la referencia al libro.

        Args:
            precio (Precio): Precio a quitar.

        Raises:
            ValueError: Si el precio no pertenece al libro.
        """
        if precio not in self.__precios:
            raise ValueError("El precio no pertenece a este libro")
        self.__precios.remove(precio)
        precio.libro = None

    def precio_en(self, codigo_moneda: str) -> Optional[Precio]:
        """Busca el precio del libro en una moneda.

        Args:
            codigo_moneda (str): Código de la moneda (sin distinguir caso).

        Returns:
            Optional[Precio]: El precio, o None si no hay uno en esa moneda.
        """
        codigo = codigo_moneda.upper()
        for precio in self.__precios:
            if precio.moneda.codigo == codigo:
                return precio
        return None

    @property
    def stock(self) -> Optional[Stock]:
        """Stock del libro (None si aún no tiene)."""
        return self.__stock

    @stock.setter
    def stock(self, valor: Optional[Stock]) -> None:
        """Asigna el stock del libro y le asigna la referencia al libro.

        Raises:
            ValueError: Si no es un Stock ni None.
        """
        if valor is not None and not isinstance(valor, Stock):
            raise ValueError("El stock debe ser una instancia de Stock")
        if valor is not None:
            valor.libro = self
        self.__stock = valor

    def __str__(self) -> str:
        """Devuelve el título, autor, editorial y precios del libro."""
        precios = ", ".join(str(p) for p in self.__precios) or "sin precio"
        return (
            f"'{self.__titulo}' de {self.__autor} "
            f"({self.__editorial.nombre}) - {precios}"
        )

    def __repr__(self) -> str:
        """Devuelve una representación técnica del libro."""
        return (
            f"Libro(id_libro={self.__id_libro}, isbn='{self.__isbn}', "
            f"titulo='{self.__titulo}')"
        )


class PrecioWeb(EntidadBase):
    """Precio de un libro observado en el sitio de un competidor.

    Cada registro se obtiene al ejecutar el scraper y queda asociado al
    libro del catálogo con el que se buscó.
    """

    def __init__(self, libro: Libro, posicion: int, titulo_web: str,
                 url: str, precio_web: float, fecha_extraccion: datetime,
                 id_precio_web: Optional[int] = None,
                 isbn_web: Optional[str] = None,
                 url_imagen: Optional[str] = None,
                 formas_pago: Optional[str] = None,
                 descripcion: Optional[str] = None,
                 coincide: bool = False,
                 similitud: Optional[float] = None) -> None:
        """Crea un precio web.

        Args:
            libro (Libro): Libro del catálogo con el que se buscó.
            posicion (int): Posición del resultado en la búsqueda (1..10).
            titulo_web (str): Título informado por el sitio.
            url (str): URL de la ficha del producto.
            precio_web (float): Precio en pesos informado por el sitio.
            fecha_extraccion (datetime): Momento de la extracción.
            id_precio_web (Optional[int]): Identificador; None si aún no se
                persistió (lo asigna la base de datos).
            isbn_web (Optional[str]): ISBN informado por el sitio.
            url_imagen (Optional[str]): URL de la imagen del producto.
            formas_pago (Optional[str]): Formas de pago como texto JSON.
            descripcion (Optional[str]): Descripción detallada.
            coincide (bool): True si el resultado es el mismo libro.
            similitud (Optional[float]): Parecido con el título interno,
                entre 0 y 1.

        Raises:
            ValueError: Si el precio es negativo o la posición no es válida.
        """
        if precio_web < 0:
            raise ValueError("El precio web no puede ser negativo")
        if posicion < 1:
            raise ValueError("La posición debe ser mayor o igual a 1")
        self.__id_precio_web = id_precio_web
        self.__libro = libro
        self.__posicion = posicion
        self.__titulo_web = titulo_web
        self.__url = url
        self.__precio_web = precio_web
        self.__fecha_extraccion = fecha_extraccion
        self.__isbn_web = isbn_web
        self.__url_imagen = url_imagen
        self.__formas_pago = formas_pago
        self.__descripcion = descripcion
        self.__coincide = coincide
        self.__similitud = similitud

    @property
    def id(self) -> Optional[int]:
        """Identificador del registro (None si aún no se persistió)."""
        return self.__id_precio_web

    @property
    def libro(self) -> Libro:
        """Libro del catálogo con el que se buscó."""
        return self.__libro

    @property
    def posicion(self) -> int:
        """Posición del resultado en la búsqueda."""
        return self.__posicion

    @property
    def titulo_web(self) -> str:
        """Título informado por el sitio."""
        return self.__titulo_web

    @property
    def url(self) -> str:
        """URL de la ficha del producto."""
        return self.__url

    @property
    def precio_web(self) -> float:
        """Precio en pesos informado por el sitio."""
        return self.__precio_web

    @property
    def fecha_extraccion(self) -> datetime:
        """Momento de la extracción."""
        return self.__fecha_extraccion

    @property
    def isbn_web(self) -> Optional[str]:
        """ISBN informado por el sitio."""
        return self.__isbn_web

    @property
    def url_imagen(self) -> Optional[str]:
        """URL de la imagen del producto."""
        return self.__url_imagen

    @property
    def formas_pago(self) -> Optional[str]:
        """Formas de pago, como texto JSON."""
        return self.__formas_pago

    @property
    def descripcion(self) -> Optional[str]:
        """Descripción detallada del producto."""
        return self.__descripcion

    @property
    def coincide(self) -> bool:
        """Indica si el resultado es el mismo libro del catálogo."""
        return self.__coincide

    @property
    def similitud(self) -> Optional[float]:
        """Parecido con el título interno, entre 0 y 1."""
        return self.__similitud

    def __repr__(self) -> str:
        """Devuelve una representación técnica del precio web."""
        return (
            f"PrecioWeb(libro={self.__libro.id}, "
            f"precio_web={self.__precio_web}, coincide={self.__coincide})"
        )


class Auditoria(EntidadBase):
    """Registro de una operación realizada en el sistema."""

    def __init__(self, accion: str, fecha: datetime,
                 detalles: Optional[str] = None,
                 id_auditoria: Optional[int] = None) -> None:
        """Crea un registro de auditoría.

        Args:
            accion (str): Acción auditada (por ejemplo, CREAR_LIBRO).
            fecha (datetime): Momento en que se ejecutó la acción.
            detalles (Optional[str]): Detalle de la operación.
            id_auditoria (Optional[int]): Identificador; None si aún no se
                persistió (lo asigna la base de datos).

        Raises:
            ValueError: Si la acción está vacía.
        """
        if not accion or not accion.strip():
            raise ValueError("La acción de auditoría no puede estar vacía")
        self.__id_auditoria = id_auditoria
        self.__accion = accion
        self.__fecha = fecha
        self.__detalles = detalles

    @property
    def id(self) -> Optional[int]:
        """Identificador del registro (None si aún no se persistió)."""
        return self.__id_auditoria

    @property
    def accion(self) -> str:
        """Acción auditada."""
        return self.__accion

    @property
    def fecha(self) -> datetime:
        """Momento en que se ejecutó la acción."""
        return self.__fecha

    @property
    def detalles(self) -> Optional[str]:
        """Detalle de la operación."""
        return self.__detalles

    def __repr__(self) -> str:
        """Devuelve una representación técnica del registro."""
        return (
            f"Auditoria(id={self.__id_auditoria}, accion='{self.__accion}')"
        )
