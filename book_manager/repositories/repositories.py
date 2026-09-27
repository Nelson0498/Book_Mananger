"""
Repositorios responsables de la persistencia de las entidades del sistema.

La persistencia se implementa sobre archivos CSV (carpeta migrations/csv),
mediante una clase base genérica (RepositorioCSV) para las entidades con
id numérico simple, y repositorios específicos para Libro, Stock y
CotizacionDolar, cuyas claves de identidad no son un simple id entero.
"""

import abc
import csv
import datetime
import os
from typing import Dict, Generic, List, Optional, TypeVar

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
    """Interfaz para el repositorio de Stock, asociado a un libro por ISBN."""

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
        self._ruta_csv = ruta_csv
        self._encabezados = encabezados
        self._asegurar_archivo()

    def _asegurar_archivo(self) -> None:
        directorio = os.path.dirname(self._ruta_csv)
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        if not os.path.exists(self._ruta_csv):
            self._escribir_filas([])

    def _leer_filas(self) -> List[Dict[str, str]]:
        with open(self._ruta_csv, mode="r", newline="",
                  encoding="utf-8") as archivo:
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
        ruta_csv: str = "book_manager/migrations/csv/generos.csv",
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
        ruta_csv: str = "book_manager/migrations/csv/editoriales.csv",
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
        ruta_csv: str = "book_manager/migrations/csv/monedas.csv",
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
        ruta_csv: str = "book_manager/migrations/csv/tipos_cotizacion.csv",
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
        ruta_csv: str = "book_manager/migrations/csv/precios.csv",
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
        ruta_csv: str = "book_manager/migrations/csv/libros.csv",
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
        ruta_csv: str = "book_manager/migrations/csv/stock.csv",
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
        ruta_csv: str = "book_manager/migrations/csv/cotizaciones.csv",
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