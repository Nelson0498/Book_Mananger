"""
Repositorios responsables de la persistencia de las entidades del sistema.

El módulo contiene dos familias de repositorios que implementan las mismas
interfaces, de modo que los servicios no dependan del mecanismo de persistencia:

- **Archivos CSV** (Sprint 1): `RepositorioCSV` como clase base genérica para
  las entidades con id numérico simple, y repositorios específicos para Libro,
  Stock y CotizacionDolar, cuyas claves de identidad no son un id entero.
  Los CSV de `migrations/csv` se conservan como fuente de la migración.

- **Base de datos relacional** (Sprint 2): `RepositorioSQLAlchemy` y sus
  repositorios derivados, que persisten mediante los modelos ORM declarados en
  `models/models.py`. La conversión entre modelos ORM y entidades de dominio se
  realiza únicamente en este módulo: las entidades conservan su encapsulamiento
  y no conocen la base de datos.
"""

import abc
import csv
import datetime
import os
from decimal import Decimal
from typing import ClassVar, Dict, Generic, List, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    CotizacionDolar,
    EntidadBase,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.models.models import (
    Base,
    CotizacionDolarModel,
    EditorialModel,
    GeneroModel,
    LibroModel,
    MonedaModel,
    PrecioModel,
    StockModel,
    TipoCotizacionModel,
)

T = TypeVar('T', bound=EntidadBase)


# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------

class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios que manejan entidades con id numérico."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea una nueva entidad en el repositorio.

        Raises:
            ValueError: Si ya existe una entidad con el mismo id.
        """

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> Optional[T]:
        """Devuelve la entidad con el id dado, o None si no existe."""

    @abc.abstractmethod
    def leer_todos(self) -> List[T]:
        """Devuelve todas las entidades del repositorio."""

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente.

        Raises:
            ValueError: Si no se encuentra la entidad para actualizar.
        """

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        """Elimina la entidad con el id dado. Devuelve True si existía."""


class IRepositorioLibro(abc.ABC):
    """Interfaz para el repositorio de Libro, identificado por ISBN."""

    @abc.abstractmethod
    def crear(self, libro: Libro) -> Libro:
        """Crea un nuevo libro.

        Raises:
            ValueError: Si ya existe un libro con el mismo ISBN.
        """

    @abc.abstractmethod
    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Devuelve el libro con el ISBN dado, o None si no existe."""

    @abc.abstractmethod
    def leer_todos(self) -> List[Libro]:
        """Devuelve todos los libros del catálogo."""

    @abc.abstractmethod
    def actualizar(self, libro: Libro) -> Libro:
        """Actualiza un libro existente.

        Raises:
            ValueError: Si no se encuentra el libro para actualizar.
        """

    @abc.abstractmethod
    def eliminar(self, isbn: str) -> bool:
        """Elimina el libro con el ISBN dado. Devuelve True si existía."""


class IRepositorioStock(abc.ABC):
    """Interfaz para el repositorio de Stock, asociado a un libro por ISBN.

    Decisión de diseño: en este modelo el identificador del libro es el ISBN
    (es la clave de la tabla `libros`, la clave de los CSV de origen y la del
    repositorio de libros), por lo que el stock se busca y se elimina por ISBN
    en lugar de por un id entero.

    La interfaz provista por la cátedra en el TP1 declaraba
    `leer_por_libro(libro_id: int)` y `eliminar(libro_id: int)`. La diferencia
    entre ambas firmas quedó registrada como observación en la devolución de
    ese trabajo y no fue resuelta oficialmente; se mantiene el ISBN para no
    introducir un identificador nuevo en `Libro` ni migrar los datos del TP1.
    """

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro de stock (stock.libro_isbn debe estar seteado).

        Raises:
            ValueError: Si ya existe stock para ese libro.
        """

    @abc.abstractmethod
    def leer_por_libro(self, libro_isbn: str) -> Optional[Stock]:
        """Devuelve el stock asociado al ISBN de libro dado, o None."""

    @abc.abstractmethod
    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza el registro de stock de un libro.

        Raises:
            ValueError: Si no se encuentra stock para ese libro.
        """

    @abc.abstractmethod
    def eliminar(self, libro_isbn: str) -> bool:
        """Elimina el stock asociado al ISBN dado. Devuelve True si existía."""


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para el repositorio de CotizacionDolar, clave (tipo, fecha)."""

    @abc.abstractmethod
    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una nueva cotización.

        Raises:
            ValueError: Si ya existe una cotización para el mismo tipo y fecha.
        """

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        """Devuelve la cotización para un tipo y fecha dados, o None."""

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve el histórico de cotizaciones de un tipo dado."""

    @abc.abstractmethod
    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza una cotización existente."""

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Elimina la cotización de un tipo y fecha dados."""


# ---------------------------------------------------------------------------
# Utilidad interna de acceso a CSV
# ---------------------------------------------------------------------------

class _AlmacenCSV:
    """Utilidad interna para leer y escribir filas de un archivo CSV.

    No forma parte del contrato público de los repositorios; solo evita
    duplicar la lógica de acceso a disco entre las distintas clases.
    """

    def __init__(self, ruta_csv: str, encabezados: List[str]) -> None:
        # Raíz del repositorio: repositories/ -> book_manager/ -> src/ -> raíz.
        raiz_proyecto = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "..", "..")
        )

        if os.path.isabs(ruta_csv):
            self._ruta_csv = ruta_csv
        else:
            self._ruta_csv = os.path.normpath(
                os.path.join(raiz_proyecto, ruta_csv)
            )

        self._encabezados = encabezados
        self._asegurar_archivo()

    def _asegurar_archivo(self) -> None:
        directorio = os.path.dirname(self._ruta_csv)
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        if not os.path.exists(self._ruta_csv):
            self._escribir_filas([])

    def _leer_filas(self) -> List[Dict[str, str]]:
        # `utf-8-sig` acepta archivos con y sin BOM, de modo que un CSV guardado
        # desde otra herramienta no rompa el nombre de la primera columna. La
        # escritura se mantiene en UTF-8 sin BOM.
        with open(self._ruta_csv, mode="r", newline="",
                  encoding="utf-8-sig") as archivo:
            return list(csv.DictReader(archivo))

    def _escribir_filas(self, filas: List[Dict[str, str]]) -> None:
        with open(self._ruta_csv, mode="w", newline="",
                  encoding="utf-8") as archivo:
            escritor = csv.DictWriter(
                archivo, fieldnames=self._encabezados
            )
            escritor.writeheader()
            escritor.writerows(filas)


# ---------------------------------------------------------------------------
# Repositorio genérico para entidades con id numérico simple
# ---------------------------------------------------------------------------

class RepositorioCSV(_AlmacenCSV, IRepositorio[T], abc.ABC):
    """Repositorio base que persiste entidades de tipo T en un archivo CSV."""

    @abc.abstractmethod
    def _to_row(self, entidad: T) -> Dict[str, str]:
        """Convierte una entidad en una fila (dict) lista para el CSV."""

    @abc.abstractmethod
    def _from_row(self, fila: Dict[str, str]) -> T:
        """Reconstruye una entidad a partir de una fila del CSV."""

    def crear(self, entidad: T) -> T:
        if self.leer_por_id(entidad.id) is not None:
            raise ValueError(f"Ya existe una entidad con id {entidad.id}")
        filas = self._leer_filas()
        filas.append(self._to_row(entidad))
        self._escribir_filas(filas)
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        for fila in self._leer_filas():
            if int(fila["id"]) == id:
                return self._from_row(fila)
        return None

    def leer_todos(self) -> List[T]:
        return [self._from_row(fila) for fila in self._leer_filas()]

    def actualizar(self, entidad: T) -> T:
        filas = self._leer_filas()
        for indice, fila in enumerate(filas):
            if int(fila["id"]) == entidad.id:
                filas[indice] = self._to_row(entidad)
                self._escribir_filas(filas)
                return entidad
        raise ValueError(
            f"No se encontró la entidad con id {entidad.id} para actualizar"
        )

    def eliminar(self, id: int) -> bool:
        filas = self._leer_filas()
        restantes = [fila for fila in filas if int(fila["id"]) != id]
        if len(restantes) == len(filas):
            return False
        self._escribir_filas(restantes)
        return True


# ---------------------------------------------------------------------------
# Repositorios concretos para entidades simples
# ---------------------------------------------------------------------------

class RepositorioGenero(RepositorioCSV[Genero]):
    """Repositorio CRUD de Genero."""

    def __init__(
        self,
        ruta_csv: str = "src/book_manager/migrations/csv/generos.csv",
    ) -> None:
        super().__init__(ruta_csv, encabezados=["id", "nombre"])

    def _to_row(self, entidad: Genero) -> Dict[str, str]:
        return {"id": str(entidad.id_genero), "nombre": entidad.nombre}

    def _from_row(self, fila: Dict[str, str]) -> Genero:
        return Genero(id_genero=int(fila["id"]), nombre=fila["nombre"])


class RepositorioEditorial(RepositorioCSV[Editorial]):
    """Repositorio CRUD de Editorial."""

    def __init__(
        self,
        ruta_csv: str = "src/book_manager/migrations/csv/editoriales.csv",
    ) -> None:
        super().__init__(ruta_csv, encabezados=["id", "nombre", "pais"])

    def _to_row(self, entidad: Editorial) -> Dict[str, str]:
        return {
            "id": str(entidad.id_editorial),
            "nombre": entidad.nombre,
            "pais": entidad.pais or "",
        }

    def _from_row(self, fila: Dict[str, str]) -> Editorial:
        return Editorial(
            id_editorial=int(fila["id"]),
            nombre=fila["nombre"],
            pais=fila["pais"] or None,
        )


class RepositorioMoneda(RepositorioCSV[Moneda]):
    """Repositorio CRUD de Moneda."""

    def __init__(
        self,
        ruta_csv: str = "src/book_manager/migrations/csv/monedas.csv",
    ) -> None:
        super().__init__(
            ruta_csv, encabezados=["id", "codigo", "nombre", "simbolo"]
        )

    def _to_row(self, entidad: Moneda) -> Dict[str, str]:
        return {
            "id": str(entidad.id_moneda),
            "codigo": entidad.codigo,
            "nombre": entidad.nombre,
            "simbolo": entidad.simbolo,
        }

    def _from_row(self, fila: Dict[str, str]) -> Moneda:
        return Moneda(
            id_moneda=int(fila["id"]),
            codigo=fila["codigo"],
            nombre=fila["nombre"],
            simbolo=fila["simbolo"],
        )


class RepositorioTipoCotizacion(RepositorioCSV[TipoCotizacion]):
    """Repositorio CRUD de TipoCotizacion."""

    def __init__(
        self,
        ruta_csv: str = "src/book_manager/migrations/csv/tipos_cotizacion.csv",
    ) -> None:
        super().__init__(ruta_csv, encabezados=["id", "nombre"])

    def _to_row(self, entidad: TipoCotizacion) -> Dict[str, str]:
        return {"id": str(entidad.id_tipo), "nombre": entidad.nombre}

    def _from_row(self, fila: Dict[str, str]) -> TipoCotizacion:
        return TipoCotizacion(
            id_tipo=int(fila["id"]), nombre=fila["nombre"]
        )


# ---------------------------------------------------------------------------
# Repositorio de Precio (entidad independiente con CRUD propio)
# ---------------------------------------------------------------------------

class RepositorioPrecio(RepositorioCSV[Precio]):
    """Repositorio CRUD de Precio.

    Persiste id_precio, valor y moneda_id.  Para reconstruir el objeto
    Precio completo delega en el repositorio de Moneda.
    """

    def __init__(
        self,
        repositorio_moneda: RepositorioMoneda,
        ruta_csv: str = "src/book_manager/migrations/csv/precios.csv",
    ) -> None:
        super().__init__(
            ruta_csv, encabezados=["id", "valor", "moneda_id"]
        )
        self._repositorio_moneda = repositorio_moneda

    def _to_row(self, entidad: Precio) -> Dict[str, str]:
        return {
            "id": str(entidad.id_precio),
            "valor": str(entidad.valor),
            "moneda_id": str(entidad.moneda.id_moneda),
        }

    def _from_row(self, fila: Dict[str, str]) -> Precio:
        moneda = self._repositorio_moneda.leer_por_id(int(fila["moneda_id"]))
        if moneda is None:
            raise ValueError(
                f"Moneda inexistente con id {fila['moneda_id']} "
                f"referenciada por el precio {fila['id']}"
            )
        return Precio(
            id_precio=int(fila["id"]),
            valor=float(fila["valor"]),
            moneda=moneda,
        )


# ---------------------------------------------------------------------------
# Repositorio de Libro (clave: ISBN, con referencias a otros repositorios)
# ---------------------------------------------------------------------------

class RepositorioLibro(_AlmacenCSV, IRepositorioLibro):
    """Repositorio CRUD de Libro.

    Persiste únicamente los ids de género, editorial y precio; para
    reconstruir el objeto completo delega en los repositorios de esas
    entidades y en el repositorio de Stock (relación 1 a 1 por ISBN).
    """

    def __init__(
        self,
        repositorio_genero: RepositorioGenero,
        repositorio_editorial: RepositorioEditorial,
        repositorio_precio: RepositorioPrecio,
        repositorio_stock: "RepositorioStock",
        ruta_csv: str = "src/book_manager/migrations/csv/libros.csv",
    ) -> None:
        super().__init__(
            ruta_csv,
            encabezados=[
                "isbn", "titulo", "autor",
                "editorial_id", "genero_id", "precio_id",
            ],
        )
        self._repositorio_genero = repositorio_genero
        self._repositorio_editorial = repositorio_editorial
        self._repositorio_precio = repositorio_precio
        self._repositorio_stock = repositorio_stock

    def _to_row(self, libro: Libro) -> Dict[str, str]:
        return {
            "isbn": libro.isbn,
            "titulo": libro.titulo,
            "autor": libro.autor,
            "editorial_id": str(libro.editorial.id_editorial),
            "genero_id": str(libro.genero.id_genero),
            "precio_id": str(libro.precio.id_precio),
        }

    def _from_row(self, fila: Dict[str, str]) -> Libro:
        genero = self._repositorio_genero.leer_por_id(
            int(fila["genero_id"])
        )
        editorial = self._repositorio_editorial.leer_por_id(
            int(fila["editorial_id"])
        )
        precio = self._repositorio_precio.leer_por_id(
            int(fila["precio_id"])
        )

        if genero is None:
            raise ValueError(
                f"Género inexistente (id={fila['genero_id']}) "
                f"para el libro {fila['isbn']}"
            )
        if editorial is None:
            raise ValueError(
                f"Editorial inexistente (id={fila['editorial_id']}) "
                f"para el libro {fila['isbn']}"
            )
        if precio is None:
            raise ValueError(
                f"Precio inexistente (id={fila['precio_id']}) "
                f"para el libro {fila['isbn']}"
            )

        stock = self._repositorio_stock.leer_por_libro(fila["isbn"])
        if stock is None:
            stock = Stock(
                id_stock=0, cantidad=0, libro_isbn=fila["isbn"]
            )

        return Libro(
            isbn=fila["isbn"],
            titulo=fila["titulo"],
            autor=fila["autor"],
            editorial=editorial,
            genero=genero,
            precio=precio,
            stock=stock,
        )

    def crear(self, libro: Libro) -> Libro:
        if self.leer_por_isbn(libro.isbn) is not None:
            raise ValueError(
                f"Ya existe un libro con ISBN {libro.isbn}"
            )
        filas = self._leer_filas()
        filas.append(self._to_row(libro))
        self._escribir_filas(filas)
        return libro

    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        for fila in self._leer_filas():
            if fila["isbn"] == isbn:
                return self._from_row(fila)
        return None

    def leer_todos(self) -> List[Libro]:
        return [self._from_row(fila) for fila in self._leer_filas()]

    def actualizar(self, libro: Libro) -> Libro:
        filas = self._leer_filas()
        for indice, fila in enumerate(filas):
            if fila["isbn"] == libro.isbn:
                filas[indice] = self._to_row(libro)
                self._escribir_filas(filas)
                return libro
        raise ValueError(
            f"No se encontró el libro con ISBN {libro.isbn} para actualizar"
        )

    def eliminar(self, isbn: str) -> bool:
        filas = self._leer_filas()
        restantes = [fila for fila in filas if fila["isbn"] != isbn]
        if len(restantes) == len(filas):
            return False
        self._escribir_filas(restantes)
        return True


# ---------------------------------------------------------------------------
# Repositorio de Stock (clave: ISBN del libro asociado)
# ---------------------------------------------------------------------------

class RepositorioStock(_AlmacenCSV, IRepositorioStock):
    """Repositorio CRUD de Stock, asociado 1 a 1 con un libro por ISBN."""

    def __init__(
        self,
        ruta_csv: str = "src/book_manager/migrations/csv/stock.csv",
    ) -> None:
        super().__init__(
            ruta_csv,
            encabezados=[
                "libro_isbn", "id_stock", "cantidad", "cantidad_minima",
            ],
        )

    def _to_row(self, stock: Stock) -> Dict[str, str]:
        if not stock.libro_isbn:
            raise ValueError(
                "El stock debe tener asignado el ISBN del libro asociado"
            )
        return {
            "libro_isbn": stock.libro_isbn,
            "id_stock": str(stock.id_stock),
            "cantidad": str(stock.cantidad),
            "cantidad_minima": str(stock.cantidad_minima),
        }

    def _from_row(self, fila: Dict[str, str]) -> Stock:
        return Stock(
            id_stock=int(fila["id_stock"]),
            cantidad=int(fila["cantidad"]),
            cantidad_minima=int(fila["cantidad_minima"]),
            libro_isbn=fila["libro_isbn"],
        )

    def crear(self, stock: Stock) -> Stock:
        if self.leer_por_libro(stock.libro_isbn) is not None:
            raise ValueError(
                f"Ya existe stock para el libro {stock.libro_isbn}"
            )
        filas = self._leer_filas()
        filas.append(self._to_row(stock))
        self._escribir_filas(filas)
        return stock

    def leer_por_libro(self, libro_isbn: str) -> Optional[Stock]:
        for fila in self._leer_filas():
            if fila["libro_isbn"] == libro_isbn:
                return self._from_row(fila)
        return None

    def leer_todos(self) -> List[Stock]:
        """Devuelve todos los registros de stock."""
        return [self._from_row(fila) for fila in self._leer_filas()]

    def actualizar(self, stock: Stock) -> Stock:
        filas = self._leer_filas()
        for indice, fila in enumerate(filas):
            if fila["libro_isbn"] == stock.libro_isbn:
                filas[indice] = self._to_row(stock)
                self._escribir_filas(filas)
                return stock
        raise ValueError(
            f"No se encontró stock para el libro {stock.libro_isbn}"
        )

    def eliminar(self, libro_isbn: str) -> bool:
        filas = self._leer_filas()
        restantes = [
            fila for fila in filas
            if fila["libro_isbn"] != libro_isbn
        ]
        if len(restantes) == len(filas):
            return False
        self._escribir_filas(restantes)
        return True


# ---------------------------------------------------------------------------
# Repositorio de CotizacionDolar (clave compuesta: tipo + fecha)
# ---------------------------------------------------------------------------

class RepositorioCotizacionDolar(_AlmacenCSV, IRepositorioCotizacionDolar):
    """Repositorio CRUD de CotizacionDolar, con clave compuesta (tipo, fecha)."""

    def __init__(
        self,
        repositorio_tipo_cotizacion: RepositorioTipoCotizacion,
        ruta_csv: str = "src/book_manager/migrations/csv/cotizaciones.csv",
    ) -> None:
        super().__init__(
            ruta_csv,
            encabezados=[
                "id_cotizacion", "tipo_id",
                "valor_compra", "valor_venta", "fecha",
            ],
        )
        self._repositorio_tipo_cotizacion = repositorio_tipo_cotizacion

    def _to_row(self, cotizacion: CotizacionDolar) -> Dict[str, str]:
        return {
            "id_cotizacion": str(cotizacion.id_cotizacion),
            "tipo_id": str(cotizacion.tipo.id_tipo),
            "valor_compra": str(cotizacion.valor_compra),
            "valor_venta": str(cotizacion.valor_venta),
            "fecha": cotizacion.fecha.isoformat(),
        }

    def _from_row(self, fila: Dict[str, str]) -> CotizacionDolar:
        tipo = self._repositorio_tipo_cotizacion.leer_por_id(
            int(fila["tipo_id"])
        )
        if tipo is None:
            raise ValueError(
                f"Tipo de cotización inexistente: {fila['tipo_id']}"
            )
        return CotizacionDolar(
            id_cotizacion=int(fila["id_cotizacion"]),
            tipo=tipo,
            valor_compra=float(fila["valor_compra"]),
            valor_venta=float(fila["valor_venta"]),
            fecha=datetime.date.fromisoformat(fila["fecha"]),
        )

    def leer_todos(self) -> List[CotizacionDolar]:
        """Devuelve todas las cotizaciones registradas."""
        return [self._from_row(fila) for fila in self._leer_filas()]

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        existente = self.leer_por_tipo_y_fecha(
            cotizacion.tipo.id_tipo, cotizacion.fecha
        )
        if existente is not None:
            raise ValueError(
                f"Ya existe una cotización de tipo "
                f"{cotizacion.tipo.id_tipo} "
                f"para la fecha {cotizacion.fecha}"
            )
        filas = self._leer_filas()
        filas.append(self._to_row(cotizacion))
        self._escribir_filas(filas)
        return cotizacion

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        for fila in self._leer_filas():
            if (int(fila["tipo_id"]) == tipo_id
                    and fila["fecha"] == fecha.isoformat()):
                return self._from_row(fila)
        return None

    def leer_historico_por_tipo(
        self, tipo_id: int
    ) -> List[CotizacionDolar]:
        return [
            self._from_row(fila)
            for fila in self._leer_filas()
            if int(fila["tipo_id"]) == tipo_id
        ]

    def actualizar(
        self, cotizacion: CotizacionDolar
    ) -> CotizacionDolar:
        filas = self._leer_filas()
        for indice, fila in enumerate(filas):
            if (int(fila["tipo_id"]) == cotizacion.tipo.id_tipo
                    and fila["fecha"] == cotizacion.fecha.isoformat()):
                filas[indice] = self._to_row(cotizacion)
                self._escribir_filas(filas)
                return cotizacion
        raise ValueError("No se encontró la cotización a actualizar")

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        filas = self._leer_filas()
        restantes = [
            fila for fila in filas
            if not (int(fila["tipo_id"]) == tipo_id
                    and fila["fecha"] == fecha.isoformat())
        ]
        if len(restantes) == len(filas):
            return False
        self._escribir_filas(restantes)
        return True


# ===========================================================================
# Sprint 2: repositorios sobre base de datos relacional (SQLAlchemy)
# ===========================================================================
#
# Implementan las mismas interfaces que los repositorios CSV, por lo que los
# servicios y la consola siguen funcionando sin modificaciones. Las lecturas
# usan `ConexionDB.obtener_sesion()` y las escrituras `ConexionDB.transaccion()`,
# de modo que cada operación de escritura se confirma o se revierte completa.


# ---------------------------------------------------------------------------
# Conversión de modelos ORM a entidades de dominio
# ---------------------------------------------------------------------------

def _genero_desde_modelo(modelo: GeneroModel) -> Genero:
    """Convierte un modelo ORM de género en su entidad de dominio."""
    return Genero(id_genero=modelo.id, nombre=modelo.nombre)


def _editorial_desde_modelo(modelo: EditorialModel) -> Editorial:
    """Convierte un modelo ORM de editorial en su entidad de dominio."""
    return Editorial(
        id_editorial=modelo.id, nombre=modelo.nombre, pais=modelo.pais
    )


def _moneda_desde_modelo(modelo: MonedaModel) -> Moneda:
    """Convierte un modelo ORM de moneda en su entidad de dominio."""
    return Moneda(
        id_moneda=modelo.id,
        codigo=modelo.codigo,
        nombre=modelo.nombre,
        simbolo=modelo.simbolo,
    )


def _tipo_cotizacion_desde_modelo(
    modelo: TipoCotizacionModel,
) -> TipoCotizacion:
    """Convierte un modelo ORM de tipo de cotización en su entidad."""
    return TipoCotizacion(id_tipo=modelo.id, nombre=modelo.nombre)


def _precio_desde_modelo(modelo: PrecioModel) -> Precio:
    """Convierte un modelo ORM de precio en su entidad de dominio.

    La base de datos devuelve `Decimal` y la entidad de dominio espera `float`,
    por lo que la conversión se hace de forma explícita.
    """
    return Precio(
        id_precio=modelo.id,
        valor=float(modelo.valor),
        moneda=_moneda_desde_modelo(modelo.moneda),
    )


def _stock_desde_modelo(modelo: StockModel) -> Stock:
    """Convierte un modelo ORM de stock en su entidad de dominio."""
    return Stock(
        id_stock=modelo.id_stock,
        cantidad=modelo.cantidad,
        cantidad_minima=modelo.cantidad_minima,
        libro_isbn=modelo.libro_isbn,
    )


def _cotizacion_desde_modelo(
    modelo: CotizacionDolarModel,
) -> CotizacionDolar:
    """Convierte un modelo ORM de cotización en su entidad de dominio."""
    return CotizacionDolar(
        id_cotizacion=modelo.id_cotizacion,
        tipo=_tipo_cotizacion_desde_modelo(modelo.tipo),
        valor_compra=float(modelo.valor_compra),
        valor_venta=float(modelo.valor_venta),
        fecha=modelo.fecha,
    )


def _libro_desde_modelo(modelo: LibroModel) -> Libro:
    """Convierte un modelo ORM de libro en su entidad de dominio.

    Si el libro todavía no tiene stock asociado se usa el mismo criterio que en
    el repositorio CSV: un stock vacío en lugar de un error.
    """
    if modelo.stock is not None:
        stock = _stock_desde_modelo(modelo.stock)
    else:
        stock = Stock(id_stock=0, cantidad=0, libro_isbn=modelo.isbn)

    return Libro(
        isbn=modelo.isbn,
        titulo=modelo.titulo,
        autor=modelo.autor,
        editorial=_editorial_desde_modelo(modelo.editorial),
        genero=_genero_desde_modelo(modelo.genero),
        precio=_precio_desde_modelo(modelo.precio),
        stock=stock,
    )


# ---------------------------------------------------------------------------
# Repositorio genérico para entidades con id numérico simple
# ---------------------------------------------------------------------------

class RepositorioSQLAlchemy(IRepositorio[T], abc.ABC):
    """Repositorio base que persiste entidades de tipo T en una base de datos.

    Attributes:
        modelo (ClassVar[type[Base]]): Modelo ORM administrado por el
            repositorio. Cada repositorio concreto debe declararlo.
    """

    modelo: ClassVar[type[Base]]

    def __init__(self, conexion: ConexionDB) -> None:
        self._conexion = conexion

    @abc.abstractmethod
    def _to_entidad(self, modelo: Base) -> T:
        """Convierte un modelo ORM en su entidad de dominio."""

    @abc.abstractmethod
    def _to_modelo(self, entidad: T) -> Base:
        """Convierte una entidad de dominio en un modelo ORM nuevo."""

    @abc.abstractmethod
    def _actualizar_modelo(self, modelo: Base, entidad: T) -> None:
        """Copia sobre un modelo ORM existente los datos de la entidad."""

    def _opciones_carga(self) -> tuple:
        """Opciones de carga anticipada de relaciones, para evitar N+1."""
        return ()

    def _buscar(self, sesion: Session, id_entidad: int) -> Optional[Base]:
        """Devuelve el modelo con la clave dada, o None si no existe."""
        return sesion.get(self.modelo, id_entidad)

    def crear(self, entidad: T) -> T:
        with self._conexion.transaccion() as sesion:
            if self._buscar(sesion, entidad.id) is not None:
                raise ValueError(f"Ya existe una entidad con id {entidad.id}")
            modelo = self._to_modelo(entidad)
            sesion.add(modelo)
            sesion.flush()
            return self._to_entidad(modelo)

    def leer_por_id(self, id: int) -> Optional[T]:
        with self._conexion.obtener_sesion() as sesion:
            modelo = self._buscar(sesion, id)
            if modelo is None:
                return None
            return self._to_entidad(modelo)

    def leer_todos(self) -> List[T]:
        with self._conexion.obtener_sesion() as sesion:
            columna_pk = self.modelo.__mapper__.primary_key[0]
            sentencia = (
                select(self.modelo)
                .options(*self._opciones_carga())
                .order_by(columna_pk)
            )
            modelos = sesion.execute(sentencia).scalars().all()
            return [self._to_entidad(modelo) for modelo in modelos]

    def actualizar(self, entidad: T) -> T:
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, entidad.id)
            if modelo is None:
                raise ValueError(
                    f"No se encontró la entidad con id {entidad.id} "
                    f"para actualizar"
                )
            self._actualizar_modelo(modelo, entidad)
            sesion.flush()
            # Se refresca el modelo para que la entidad devuelta refleje el
            # estado persistido, incluidas las relaciones recargadas.
            sesion.expire(modelo)
            return self._to_entidad(modelo)

    def eliminar(self, id: int) -> bool:
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, id)
            if modelo is None:
                return False
            sesion.delete(modelo)
            return True


# ---------------------------------------------------------------------------
# Repositorios concretos para entidades simples
# ---------------------------------------------------------------------------

class RepositorioGeneroSQLAlchemy(RepositorioSQLAlchemy[Genero]):
    """Repositorio CRUD de Genero sobre la tabla `generos`."""

    modelo = GeneroModel

    def _to_entidad(self, modelo: GeneroModel) -> Genero:
        return _genero_desde_modelo(modelo)

    def _to_modelo(self, entidad: Genero) -> GeneroModel:
        return GeneroModel(id=entidad.id_genero, nombre=entidad.nombre)

    def _actualizar_modelo(self, modelo: GeneroModel,
                           entidad: Genero) -> None:
        modelo.nombre = entidad.nombre


class RepositorioEditorialSQLAlchemy(RepositorioSQLAlchemy[Editorial]):
    """Repositorio CRUD de Editorial sobre la tabla `editoriales`."""

    modelo = EditorialModel

    def _to_entidad(self, modelo: EditorialModel) -> Editorial:
        return _editorial_desde_modelo(modelo)

    def _to_modelo(self, entidad: Editorial) -> EditorialModel:
        return EditorialModel(
            id=entidad.id_editorial,
            nombre=entidad.nombre,
            pais=entidad.pais,
        )

    def _actualizar_modelo(self, modelo: EditorialModel,
                           entidad: Editorial) -> None:
        modelo.nombre = entidad.nombre
        modelo.pais = entidad.pais


class RepositorioMonedaSQLAlchemy(RepositorioSQLAlchemy[Moneda]):
    """Repositorio CRUD de Moneda sobre la tabla `monedas`."""

    modelo = MonedaModel

    def _to_entidad(self, modelo: MonedaModel) -> Moneda:
        return _moneda_desde_modelo(modelo)

    def _to_modelo(self, entidad: Moneda) -> MonedaModel:
        return MonedaModel(
            id=entidad.id_moneda,
            codigo=entidad.codigo,
            nombre=entidad.nombre,
            simbolo=entidad.simbolo,
        )

    def _actualizar_modelo(self, modelo: MonedaModel,
                           entidad: Moneda) -> None:
        modelo.codigo = entidad.codigo
        modelo.nombre = entidad.nombre
        modelo.simbolo = entidad.simbolo


class RepositorioTipoCotizacionSQLAlchemy(
    RepositorioSQLAlchemy[TipoCotizacion]
):
    """Repositorio CRUD de TipoCotizacion sobre la tabla `tipos_cotizacion`."""

    modelo = TipoCotizacionModel

    def _to_entidad(self, modelo: TipoCotizacionModel) -> TipoCotizacion:
        return _tipo_cotizacion_desde_modelo(modelo)

    def _to_modelo(self, entidad: TipoCotizacion) -> TipoCotizacionModel:
        return TipoCotizacionModel(id=entidad.id_tipo, nombre=entidad.nombre)

    def _actualizar_modelo(self, modelo: TipoCotizacionModel,
                           entidad: TipoCotizacion) -> None:
        modelo.nombre = entidad.nombre


class RepositorioPrecioSQLAlchemy(RepositorioSQLAlchemy[Precio]):
    """Repositorio CRUD de Precio sobre la tabla `precios`.

    La conversión a `Decimal` se hace a partir de la representación textual del
    valor para evitar los errores de redondeo del punto flotante binario.
    """

    modelo = PrecioModel

    def _opciones_carga(self) -> tuple:
        return (selectinload(PrecioModel.moneda),)

    def _to_entidad(self, modelo: PrecioModel) -> Precio:
        return _precio_desde_modelo(modelo)

    def _to_modelo(self, entidad: Precio) -> PrecioModel:
        return PrecioModel(
            id=entidad.id_precio,
            valor=Decimal(str(entidad.valor)),
            moneda_id=entidad.moneda.id_moneda,
        )

    def _actualizar_modelo(self, modelo: PrecioModel,
                           entidad: Precio) -> None:
        modelo.valor = Decimal(str(entidad.valor))
        modelo.moneda_id = entidad.moneda.id_moneda

    def eliminar(self, id: int) -> bool:
        """Elimina un precio, siempre que ningún libro dependa de él.

        Un precio referenciado por un libro no puede borrarse de forma
        independiente: la clave foránea `libros.precio_id` no admite nulos. Se
        informa con un error claro en lugar de dejar que la base falle, y el
        precio se elimina junto con su libro desde `ServicioLibro.eliminar`.

        Raises:
            ValueError: Si el precio está asociado a un libro.
        """
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, id)
            if modelo is None:
                return False

            libro = sesion.execute(
                select(LibroModel).where(LibroModel.precio_id == id)
            ).scalars().first()
            if libro is not None:
                raise ValueError(
                    f"El precio {id} está asociado al libro {libro.isbn} "
                    f"y no puede eliminarse por separado"
                )

            sesion.delete(modelo)
            return True


# ---------------------------------------------------------------------------
# Repositorio de Libro (clave: ISBN)
# ---------------------------------------------------------------------------

class RepositorioLibroSQLAlchemy(IRepositorioLibro):
    """Repositorio CRUD de Libro sobre la tabla `libros`."""

    # Carga anticipada de las relaciones necesarias para reconstruir el libro
    # completo sin una consulta por cada registro del listado.
    _OPCIONES_CARGA = (
        selectinload(LibroModel.genero),
        selectinload(LibroModel.editorial),
        selectinload(LibroModel.precio).selectinload(PrecioModel.moneda),
        selectinload(LibroModel.stock),
    )

    def __init__(self, conexion: ConexionDB) -> None:
        self._conexion = conexion

    def _buscar(self, sesion: Session, isbn: str) -> Optional[LibroModel]:
        sentencia = (
            select(LibroModel)
            .options(*self._OPCIONES_CARGA)
            .where(LibroModel.isbn == isbn)
        )
        return sesion.execute(sentencia).scalars().first()

    def _to_modelo(self, libro: Libro) -> LibroModel:
        return LibroModel(
            isbn=libro.isbn,
            titulo=libro.titulo,
            autor=libro.autor,
            editorial_id=libro.editorial.id_editorial,
            genero_id=libro.genero.id_genero,
            precio_id=libro.precio.id_precio,
        )

    def crear(self, libro: Libro) -> Libro:
        with self._conexion.transaccion() as sesion:
            if self._buscar(sesion, libro.isbn) is not None:
                raise ValueError(f"Ya existe un libro con ISBN {libro.isbn}")
            sesion.add(self._to_modelo(libro))
            sesion.flush()
            return _libro_desde_modelo(self._buscar(sesion, libro.isbn))

    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        with self._conexion.obtener_sesion() as sesion:
            modelo = self._buscar(sesion, isbn)
            if modelo is None:
                return None
            return _libro_desde_modelo(modelo)

    def leer_todos(self) -> List[Libro]:
        with self._conexion.obtener_sesion() as sesion:
            sentencia = (
                select(LibroModel)
                .options(*self._OPCIONES_CARGA)
                .order_by(LibroModel.isbn)
            )
            modelos = sesion.execute(sentencia).scalars().all()
            return [_libro_desde_modelo(modelo) for modelo in modelos]

    def actualizar(self, libro: Libro) -> Libro:
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, libro.isbn)
            if modelo is None:
                raise ValueError(
                    f"No se encontró el libro con ISBN {libro.isbn} "
                    f"para actualizar"
                )
            modelo.titulo = libro.titulo
            modelo.autor = libro.autor
            modelo.editorial_id = libro.editorial.id_editorial
            modelo.genero_id = libro.genero.id_genero
            modelo.precio_id = libro.precio.id_precio
            sesion.flush()
            sesion.expire(modelo)
            return _libro_desde_modelo(self._buscar(sesion, libro.isbn))

    def eliminar(self, isbn: str) -> bool:
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, isbn)
            if modelo is None:
                return False
            sesion.delete(modelo)
            return True


# ---------------------------------------------------------------------------
# Repositorio de Stock (clave: ISBN del libro asociado)
# ---------------------------------------------------------------------------

class RepositorioStockSQLAlchemy(IRepositorioStock):
    """Repositorio CRUD de Stock sobre la tabla `stock`."""

    def __init__(self, conexion: ConexionDB) -> None:
        self._conexion = conexion

    def _buscar(self, sesion: Session, libro_isbn: str) -> Optional[StockModel]:
        sentencia = select(StockModel).where(
            StockModel.libro_isbn == libro_isbn
        )
        return sesion.execute(sentencia).scalars().first()

    def _validar_libro(self, stock: Stock) -> str:
        if not stock.libro_isbn:
            raise ValueError(
                "El stock debe tener asignado el ISBN del libro asociado"
            )
        return stock.libro_isbn

    def crear(self, stock: Stock) -> Stock:
        libro_isbn = self._validar_libro(stock)
        with self._conexion.transaccion() as sesion:
            if self._buscar(sesion, libro_isbn) is not None:
                raise ValueError(
                    f"Ya existe stock para el libro {libro_isbn}"
                )
            sesion.add(
                StockModel(
                    id_stock=stock.id_stock,
                    libro_isbn=libro_isbn,
                    cantidad=stock.cantidad,
                    cantidad_minima=stock.cantidad_minima,
                )
            )
            sesion.flush()
            return _stock_desde_modelo(self._buscar(sesion, libro_isbn))

    def leer_por_libro(self, libro_isbn: str) -> Optional[Stock]:
        with self._conexion.obtener_sesion() as sesion:
            modelo = self._buscar(sesion, libro_isbn)
            if modelo is None:
                return None
            return _stock_desde_modelo(modelo)

    def leer_todos(self) -> List[Stock]:
        """Devuelve todos los registros de stock."""
        with self._conexion.obtener_sesion() as sesion:
            sentencia = select(StockModel).order_by(StockModel.id_stock)
            modelos = sesion.execute(sentencia).scalars().all()
            return [_stock_desde_modelo(modelo) for modelo in modelos]

    def actualizar(self, stock: Stock) -> Stock:
        libro_isbn = self._validar_libro(stock)
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, libro_isbn)
            if modelo is None:
                raise ValueError(
                    f"No se encontró stock para el libro {libro_isbn}"
                )
            modelo.cantidad = stock.cantidad
            modelo.cantidad_minima = stock.cantidad_minima
            sesion.flush()
            sesion.expire(modelo)
            return _stock_desde_modelo(self._buscar(sesion, libro_isbn))

    def eliminar(self, libro_isbn: str) -> bool:
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, libro_isbn)
            if modelo is None:
                return False
            sesion.delete(modelo)
            return True


# ---------------------------------------------------------------------------
# Repositorio de CotizacionDolar (clave compuesta: tipo + fecha)
# ---------------------------------------------------------------------------

class RepositorioCotizacionDolarSQLAlchemy(IRepositorioCotizacionDolar):
    """Repositorio CRUD de CotizacionDolar sobre la tabla `cotizaciones`."""

    _OPCIONES_CARGA = (selectinload(CotizacionDolarModel.tipo),)

    def __init__(self, conexion: ConexionDB) -> None:
        self._conexion = conexion

    def _buscar(
        self, sesion: Session, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolarModel]:
        sentencia = (
            select(CotizacionDolarModel)
            .options(*self._OPCIONES_CARGA)
            .where(
                CotizacionDolarModel.tipo_id == tipo_id,
                CotizacionDolarModel.fecha == fecha,
            )
        )
        return sesion.execute(sentencia).scalars().first()

    def _buscar_por_id(
        self, sesion: Session, id_cotizacion: int
    ) -> Optional[CotizacionDolarModel]:
        sentencia = (
            select(CotizacionDolarModel)
            .options(*self._OPCIONES_CARGA)
            .where(CotizacionDolarModel.id_cotizacion == id_cotizacion)
        )
        return sesion.execute(sentencia).scalars().first()

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        tipo_id = cotizacion.tipo.id_tipo
        with self._conexion.transaccion() as sesion:
            if self._buscar(sesion, tipo_id, cotizacion.fecha) is not None:
                raise ValueError(
                    f"Ya existe una cotización de tipo {tipo_id} "
                    f"para la fecha {cotizacion.fecha}"
                )
            sesion.add(
                CotizacionDolarModel(
                    id_cotizacion=cotizacion.id_cotizacion,
                    tipo_id=tipo_id,
                    valor_compra=Decimal(str(cotizacion.valor_compra)),
                    valor_venta=Decimal(str(cotizacion.valor_venta)),
                    fecha=cotizacion.fecha,
                )
            )
            sesion.flush()
            modelo = self._buscar_por_id(sesion, cotizacion.id_cotizacion)
            return _cotizacion_desde_modelo(modelo)

    def leer_por_tipo_y_fecha(
        self, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolar]:
        with self._conexion.obtener_sesion() as sesion:
            modelo = self._buscar(sesion, tipo_id, fecha)
            if modelo is None:
                return None
            return _cotizacion_desde_modelo(modelo)

    def leer_historico_por_tipo(
        self, tipo_id: int
    ) -> List[CotizacionDolar]:
        with self._conexion.obtener_sesion() as sesion:
            sentencia = (
                select(CotizacionDolarModel)
                .options(*self._OPCIONES_CARGA)
                .where(CotizacionDolarModel.tipo_id == tipo_id)
                .order_by(CotizacionDolarModel.fecha)
            )
            modelos = sesion.execute(sentencia).scalars().all()
            return [_cotizacion_desde_modelo(modelo) for modelo in modelos]

    def leer_todos(self) -> List[CotizacionDolar]:
        """Devuelve todas las cotizaciones registradas."""
        with self._conexion.obtener_sesion() as sesion:
            sentencia = (
                select(CotizacionDolarModel)
                .options(*self._OPCIONES_CARGA)
                .order_by(CotizacionDolarModel.id_cotizacion)
            )
            modelos = sesion.execute(sentencia).scalars().all()
            return [_cotizacion_desde_modelo(modelo) for modelo in modelos]

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar_por_id(sesion, cotizacion.id_cotizacion)
            if modelo is None:
                raise ValueError("No se encontró la cotización a actualizar")
            modelo.tipo_id = cotizacion.tipo.id_tipo
            modelo.valor_compra = Decimal(str(cotizacion.valor_compra))
            modelo.valor_venta = Decimal(str(cotizacion.valor_venta))
            modelo.fecha = cotizacion.fecha
            sesion.flush()
            sesion.expire(modelo)
            modelo = self._buscar_por_id(sesion, cotizacion.id_cotizacion)
            return _cotizacion_desde_modelo(modelo)

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, tipo_id, fecha)
            if modelo is None:
                return False
            sesion.delete(modelo)
            return True
