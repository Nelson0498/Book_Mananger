"""Repositorios responsables de la persistencia de las entidades del sistema.

Los repositorios persisten en una base de datos relacional mediante los
modelos ORM declarados en `models/models.py`. La conversión entre modelos ORM
y entidades de dominio se realiza únicamente en este módulo: las entidades
conservan su encapsulamiento y no conocen la base de datos.

Las lecturas usan `ConexionDB.obtener_sesion()` y las escrituras
`ConexionDB.transaccion()`, de modo que cada operación de escritura se
confirma o se revierte completa.
"""

import abc
import datetime
from decimal import Decimal
from typing import ClassVar, Generic, List, Optional, TypeVar

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

        Args:
            entidad (T): Entidad a persistir.

        Returns:
            T: La entidad persistida.

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


class IRepositorioLibro(IRepositorio[Libro]):
    """Interfaz para el repositorio de Libro, identificado por id."""

    @abc.abstractmethod
    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Devuelve el libro con el ISBN dado, o None si no existe."""


class IRepositorioStock(abc.ABC):
    """Interfaz para el repositorio de Stock, asociado a un libro por id."""

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro de stock (stock.libro debe estar seteado).

        Raises:
            ValueError: Si el stock no tiene libro o ya existe stock para él.
        """

    @abc.abstractmethod
    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Devuelve el stock asociado al id de libro dado, o None."""

    @abc.abstractmethod
    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza el registro de stock de un libro.

        Raises:
            ValueError: Si no se encuentra stock para ese libro.
        """

    @abc.abstractmethod
    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock asociado al id dado. Devuelve True si existía."""


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para el repositorio de CotizacionDolar, clave (tipo, fecha)."""

    @abc.abstractmethod
    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una nueva cotización.

        Raises:
            ValueError: Si ya existe una cotización del mismo tipo y fecha.
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


def _libro_basico_desde_modelo(modelo: LibroModel) -> Libro:
    """Convierte un libro ORM en una entidad sin precios ni stock.

    Se usa para colgar la referencia al libro en un `Precio` o un `Stock`
    leídos por separado, sin recorrer de nuevo todo el grafo de relaciones.
    """
    return Libro(
        id_libro=modelo.id,
        isbn=modelo.isbn,
        titulo=modelo.titulo,
        autor=modelo.autor,
        editorial=_editorial_desde_modelo(modelo.editorial),
        genero=_genero_desde_modelo(modelo.genero),
    )


def _precio_desde_modelo(
    modelo: PrecioModel, libro: Optional[Libro] = None
) -> Precio:
    """Convierte un modelo ORM de precio en su entidad de dominio.

    La base de datos devuelve `Decimal` y la entidad de dominio espera
    `float`, por lo que la conversión se hace de forma explícita.

    Args:
        modelo (PrecioModel): Modelo a convertir.
        libro (Optional[Libro]): Libro al que se asocia el precio. Si es
            None, se arma un libro básico a partir de la relación ORM.

    Returns:
        Precio: Entidad con su referencia al libro asignada.
    """
    precio = Precio(
        id_precio=modelo.id,
        valor=float(modelo.valor),
        moneda=_moneda_desde_modelo(modelo.moneda),
    )
    precio.libro = (
        libro if libro is not None
        else _libro_basico_desde_modelo(modelo.libro)
    )
    return precio


def _stock_desde_modelo(
    modelo: StockModel, libro: Optional[Libro] = None
) -> Stock:
    """Convierte un modelo ORM de stock en su entidad de dominio.

    Args:
        modelo (StockModel): Modelo a convertir.
        libro (Optional[Libro]): Libro al que se asocia el stock. Si es
            None, se arma un libro básico a partir de la relación ORM.

    Returns:
        Stock: Entidad con su referencia al libro asignada.
    """
    stock = Stock(
        id_stock=modelo.id_stock,
        cantidad=modelo.cantidad,
        cantidad_minima=modelo.cantidad_minima,
    )
    stock.libro = (
        libro if libro is not None
        else _libro_basico_desde_modelo(modelo.libro)
    )
    return stock


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
    """Convierte un modelo ORM de libro en su entidad de dominio completa.

    El libro se arma con todos sus precios y su stock, y cada uno recibe la
    referencia al libro (relación bidireccional).
    """
    libro = _libro_basico_desde_modelo(modelo)

    for modelo_precio in sorted(modelo.precios, key=lambda p: p.id):
        libro.agregar_precio(_precio_desde_modelo(modelo_precio, libro))

    if modelo.stock is not None:
        libro.stock = _stock_desde_modelo(modelo.stock, libro)

    return libro


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
        """Crea el repositorio.

        Args:
            conexion (ConexionDB): Conexión a la base de datos.
        """
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
        """Crea una nueva entidad en la base de datos.

        Args:
            entidad (T): Entidad a persistir.

        Returns:
            T: La entidad persistida.

        Raises:
            ValueError: Si ya existe una entidad con el mismo id.
        """
        with self._conexion.transaccion() as sesion:
            if self._buscar(sesion, entidad.id) is not None:
                raise ValueError(f"Ya existe una entidad con id {entidad.id}")
            modelo = self._to_modelo(entidad)
            sesion.add(modelo)
            sesion.flush()
            sesion.expire(modelo)
            return self._to_entidad(modelo)

    def leer_por_id(self, id: int) -> Optional[T]:
        """Devuelve la entidad con el id dado, o None si no existe."""
        with self._conexion.obtener_sesion() as sesion:
            modelo = self._buscar(sesion, id)
            if modelo is None:
                return None
            return self._to_entidad(modelo)

    def leer_todos(self) -> List[T]:
        """Devuelve todas las entidades, ordenadas por clave primaria."""
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
        """Actualiza una entidad existente.

        Raises:
            ValueError: Si no se encuentra la entidad para actualizar.
        """
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
        """Elimina la entidad con el id dado. Devuelve True si existía."""
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, id)
            if modelo is None:
                return False
            sesion.delete(modelo)
            return True


# ---------------------------------------------------------------------------
# Repositorios concretos para entidades simples
# ---------------------------------------------------------------------------

class RepositorioGenero(RepositorioSQLAlchemy[Genero]):
    """Repositorio CRUD de Genero sobre la tabla `generos`."""

    modelo = GeneroModel

    def _to_entidad(self, modelo: GeneroModel) -> Genero:
        """Convierte el modelo ORM en entidad."""
        return _genero_desde_modelo(modelo)

    def _to_modelo(self, entidad: Genero) -> GeneroModel:
        """Convierte la entidad en un modelo ORM nuevo."""
        return GeneroModel(id=entidad.id_genero, nombre=entidad.nombre)

    def _actualizar_modelo(self, modelo: GeneroModel,
                           entidad: Genero) -> None:
        """Copia los datos de la entidad sobre el modelo."""
        modelo.nombre = entidad.nombre


class RepositorioEditorial(RepositorioSQLAlchemy[Editorial]):
    """Repositorio CRUD de Editorial sobre la tabla `editoriales`."""

    modelo = EditorialModel

    def _to_entidad(self, modelo: EditorialModel) -> Editorial:
        """Convierte el modelo ORM en entidad."""
        return _editorial_desde_modelo(modelo)

    def _to_modelo(self, entidad: Editorial) -> EditorialModel:
        """Convierte la entidad en un modelo ORM nuevo."""
        return EditorialModel(
            id=entidad.id_editorial,
            nombre=entidad.nombre,
            pais=entidad.pais,
        )

    def _actualizar_modelo(self, modelo: EditorialModel,
                           entidad: Editorial) -> None:
        """Copia los datos de la entidad sobre el modelo."""
        modelo.nombre = entidad.nombre
        modelo.pais = entidad.pais


class RepositorioMoneda(RepositorioSQLAlchemy[Moneda]):
    """Repositorio CRUD de Moneda sobre la tabla `monedas`."""

    modelo = MonedaModel

    def _to_entidad(self, modelo: MonedaModel) -> Moneda:
        """Convierte el modelo ORM en entidad."""
        return _moneda_desde_modelo(modelo)

    def _to_modelo(self, entidad: Moneda) -> MonedaModel:
        """Convierte la entidad en un modelo ORM nuevo."""
        return MonedaModel(
            id=entidad.id_moneda,
            codigo=entidad.codigo,
            nombre=entidad.nombre,
            simbolo=entidad.simbolo,
        )

    def _actualizar_modelo(self, modelo: MonedaModel,
                           entidad: Moneda) -> None:
        """Copia los datos de la entidad sobre el modelo."""
        modelo.codigo = entidad.codigo
        modelo.nombre = entidad.nombre
        modelo.simbolo = entidad.simbolo


class RepositorioTipoCotizacion(RepositorioSQLAlchemy[TipoCotizacion]):
    """Repositorio CRUD de TipoCotizacion sobre `tipos_cotizacion`."""

    modelo = TipoCotizacionModel

    def _to_entidad(self, modelo: TipoCotizacionModel) -> TipoCotizacion:
        """Convierte el modelo ORM en entidad."""
        return _tipo_cotizacion_desde_modelo(modelo)

    def _to_modelo(self, entidad: TipoCotizacion) -> TipoCotizacionModel:
        """Convierte la entidad en un modelo ORM nuevo."""
        return TipoCotizacionModel(id=entidad.id_tipo, nombre=entidad.nombre)

    def _actualizar_modelo(self, modelo: TipoCotizacionModel,
                           entidad: TipoCotizacion) -> None:
        """Copia los datos de la entidad sobre el modelo."""
        modelo.nombre = entidad.nombre


# ---------------------------------------------------------------------------
# Repositorio de Precio (relación N a 1 con Libro)
# ---------------------------------------------------------------------------

class RepositorioPrecio(RepositorioSQLAlchemy[Precio]):
    """Repositorio CRUD de Precio sobre la tabla `precios`.

    La conversión a `Decimal` se hace a partir de la representación textual
    del valor para evitar los errores de redondeo del punto flotante binario.
    Cada precio se persiste asociado al libro indicado en `precio.libro`.
    """

    modelo = PrecioModel

    def _opciones_carga(self) -> tuple:
        """Carga anticipada de la moneda y del libro del precio."""
        return (
            selectinload(PrecioModel.moneda),
            selectinload(PrecioModel.libro).selectinload(
                LibroModel.editorial
            ),
            selectinload(PrecioModel.libro).selectinload(LibroModel.genero),
        )

    def _to_entidad(self, modelo: PrecioModel) -> Precio:
        """Convierte el modelo ORM en entidad."""
        return _precio_desde_modelo(modelo)

    def _to_modelo(self, entidad: Precio) -> PrecioModel:
        """Convierte la entidad en un modelo ORM nuevo.

        Raises:
            ValueError: Si el precio no tiene un libro asignado.
        """
        if entidad.libro is None:
            raise ValueError("El precio debe tener un libro asignado")
        return PrecioModel(
            id=entidad.id_precio,
            libro_id=entidad.libro.id,
            moneda_id=entidad.moneda.id_moneda,
            valor=Decimal(str(entidad.valor)),
        )

    def _actualizar_modelo(self, modelo: PrecioModel,
                           entidad: Precio) -> None:
        """Copia los datos de la entidad sobre el modelo."""
        modelo.valor = Decimal(str(entidad.valor))
        modelo.moneda_id = entidad.moneda.id_moneda

    def leer_por_libro(self, libro_id: int) -> List[Precio]:
        """Devuelve los precios de un libro, uno por moneda.

        Args:
            libro_id (int): Identificador del libro.

        Returns:
            List[Precio]: Precios del libro ordenados por id.
        """
        with self._conexion.obtener_sesion() as sesion:
            sentencia = (
                select(PrecioModel)
                .options(*self._opciones_carga())
                .where(PrecioModel.libro_id == libro_id)
                .order_by(PrecioModel.id)
            )
            modelos = sesion.execute(sentencia).scalars().all()
            return [self._to_entidad(modelo) for modelo in modelos]


# ---------------------------------------------------------------------------
# Repositorio de Libro
# ---------------------------------------------------------------------------

class RepositorioLibro(RepositorioSQLAlchemy[Libro], IRepositorioLibro):
    """Repositorio CRUD de Libro sobre la tabla `libros`.

    Persiste el libro junto con sus precios y su stock en una misma
    transacción. Al actualizar sincroniza las listas de precios y el stock.
    """

    modelo = LibroModel

    def _opciones_carga(self) -> tuple:
        """Carga anticipada de las relaciones del libro completo."""
        return (
            selectinload(LibroModel.genero),
            selectinload(LibroModel.editorial),
            selectinload(LibroModel.precios).selectinload(PrecioModel.moneda),
            selectinload(LibroModel.stock),
        )

    def _to_entidad(self, modelo: LibroModel) -> Libro:
        """Convierte el modelo ORM en entidad."""
        return _libro_desde_modelo(modelo)

    def _to_modelo(self, entidad: Libro) -> LibroModel:
        """Convierte el libro, con sus precios y stock, en un modelo ORM."""
        modelo = LibroModel(
            id=entidad.id_libro,
            isbn=entidad.isbn,
            titulo=entidad.titulo,
            autor=entidad.autor,
            editorial_id=entidad.editorial.id_editorial,
            genero_id=entidad.genero.id_genero,
        )
        modelo.precios = [
            PrecioModel(
                id=precio.id_precio,
                moneda_id=precio.moneda.id_moneda,
                valor=Decimal(str(precio.valor)),
            )
            for precio in entidad.precios
        ]
        if entidad.stock is not None:
            modelo.stock = StockModel(
                id_stock=entidad.stock.id_stock,
                cantidad=entidad.stock.cantidad,
                cantidad_minima=entidad.stock.cantidad_minima,
            )
        return modelo

    def _actualizar_modelo(self, modelo: LibroModel,
                           entidad: Libro) -> None:
        """Copia los datos del libro y sincroniza precios y stock."""
        modelo.isbn = entidad.isbn
        modelo.titulo = entidad.titulo
        modelo.autor = entidad.autor
        modelo.editorial_id = entidad.editorial.id_editorial
        modelo.genero_id = entidad.genero.id_genero

        por_id = {p.id: p for p in modelo.precios}
        ids_entidad = {p.id_precio for p in entidad.precios}
        for precio in entidad.precios:
            existente = por_id.get(precio.id_precio)
            if existente is None:
                modelo.precios.append(PrecioModel(
                    id=precio.id_precio,
                    moneda_id=precio.moneda.id_moneda,
                    valor=Decimal(str(precio.valor)),
                ))
            else:
                existente.moneda_id = precio.moneda.id_moneda
                existente.valor = Decimal(str(precio.valor))
        for id_precio, existente in por_id.items():
            if id_precio not in ids_entidad:
                modelo.precios.remove(existente)

        if entidad.stock is None:
            modelo.stock = None
        elif modelo.stock is None:
            modelo.stock = StockModel(
                id_stock=entidad.stock.id_stock,
                cantidad=entidad.stock.cantidad,
                cantidad_minima=entidad.stock.cantidad_minima,
            )
        else:
            modelo.stock.cantidad = entidad.stock.cantidad
            modelo.stock.cantidad_minima = entidad.stock.cantidad_minima

    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Devuelve el libro con el ISBN dado, o None si no existe."""
        with self._conexion.obtener_sesion() as sesion:
            sentencia = (
                select(LibroModel)
                .options(*self._opciones_carga())
                .where(LibroModel.isbn == isbn)
            )
            modelo = sesion.execute(sentencia).scalars().first()
            if modelo is None:
                return None
            return _libro_desde_modelo(modelo)


# ---------------------------------------------------------------------------
# Repositorio de Stock (clave: id del libro asociado)
# ---------------------------------------------------------------------------

class RepositorioStock(IRepositorioStock):
    """Repositorio CRUD de Stock sobre la tabla `stock` (1 a 1 con libro)."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Crea el repositorio.

        Args:
            conexion (ConexionDB): Conexión a la base de datos.
        """
        self._conexion = conexion

    _OPCIONES_CARGA = (
        selectinload(StockModel.libro).selectinload(LibroModel.editorial),
        selectinload(StockModel.libro).selectinload(LibroModel.genero),
    )

    def _buscar(self, sesion: Session, libro_id: int) -> Optional[StockModel]:
        """Devuelve el modelo de stock del libro, o None si no existe."""
        sentencia = (
            select(StockModel)
            .options(*self._OPCIONES_CARGA)
            .where(StockModel.libro_id == libro_id)
        )
        return sesion.execute(sentencia).scalars().first()

    def _validar_libro(self, stock: Stock) -> int:
        """Devuelve el id del libro del stock.

        Raises:
            ValueError: Si el stock no tiene un libro asignado.
        """
        if stock.libro is None:
            raise ValueError(
                "El stock debe tener asignado el libro asociado"
            )
        return stock.libro.id

    def crear(self, stock: Stock) -> Stock:
        """Crea un registro de stock para el libro de `stock.libro`.

        Raises:
            ValueError: Si el stock no tiene libro o ya existe stock.
        """
        libro_id = self._validar_libro(stock)
        with self._conexion.transaccion() as sesion:
            if self._buscar(sesion, libro_id) is not None:
                raise ValueError(
                    f"Ya existe stock para el libro {libro_id}"
                )
            sesion.add(
                StockModel(
                    id_stock=stock.id_stock,
                    libro_id=libro_id,
                    cantidad=stock.cantidad,
                    cantidad_minima=stock.cantidad_minima,
                )
            )
            sesion.flush()
            return _stock_desde_modelo(self._buscar(sesion, libro_id))

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Devuelve el stock del libro dado, o None si no tiene."""
        with self._conexion.obtener_sesion() as sesion:
            modelo = self._buscar(sesion, libro_id)
            if modelo is None:
                return None
            return _stock_desde_modelo(modelo)

    def leer_todos(self) -> List[Stock]:
        """Devuelve todos los registros de stock, ordenados por id."""
        with self._conexion.obtener_sesion() as sesion:
            sentencia = (
                select(StockModel)
                .options(*self._OPCIONES_CARGA)
                .order_by(StockModel.id_stock)
            )
            modelos = sesion.execute(sentencia).scalars().all()
            return [_stock_desde_modelo(modelo) for modelo in modelos]

    def actualizar(self, stock: Stock) -> Stock:
        """Actualiza las cantidades del stock del libro.

        Raises:
            ValueError: Si no hay stock registrado para ese libro.
        """
        libro_id = self._validar_libro(stock)
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, libro_id)
            if modelo is None:
                raise ValueError(
                    f"No se encontró stock para el libro {libro_id}"
                )
            modelo.cantidad = stock.cantidad
            modelo.cantidad_minima = stock.cantidad_minima
            sesion.flush()
            sesion.expire(modelo)
            return _stock_desde_modelo(self._buscar(sesion, libro_id))

    def eliminar(self, libro_id: int) -> bool:
        """Elimina el stock del libro dado. Devuelve True si existía."""
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, libro_id)
            if modelo is None:
                return False
            sesion.delete(modelo)
            return True


# ---------------------------------------------------------------------------
# Repositorio de CotizacionDolar (clave compuesta: tipo + fecha)
# ---------------------------------------------------------------------------

class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Repositorio CRUD de CotizacionDolar sobre la tabla `cotizaciones`."""

    _OPCIONES_CARGA = (selectinload(CotizacionDolarModel.tipo),)

    def __init__(self, conexion: ConexionDB) -> None:
        """Crea el repositorio.

        Args:
            conexion (ConexionDB): Conexión a la base de datos.
        """
        self._conexion = conexion

    def _buscar(
        self, sesion: Session, tipo_id: int, fecha: datetime.date
    ) -> Optional[CotizacionDolarModel]:
        """Busca el modelo por tipo y fecha."""
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
        """Busca el modelo por su identificador."""
        sentencia = (
            select(CotizacionDolarModel)
            .options(*self._OPCIONES_CARGA)
            .where(CotizacionDolarModel.id_cotizacion == id_cotizacion)
        )
        return sesion.execute(sentencia).scalars().first()

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea una cotización.

        Raises:
            ValueError: Si ya existe una del mismo tipo y fecha.
        """
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
        """Devuelve la cotización de un tipo y fecha, o None."""
        with self._conexion.obtener_sesion() as sesion:
            modelo = self._buscar(sesion, tipo_id, fecha)
            if modelo is None:
                return None
            return _cotizacion_desde_modelo(modelo)

    def leer_historico_por_tipo(
        self, tipo_id: int
    ) -> List[CotizacionDolar]:
        """Devuelve el histórico de un tipo, ordenado por fecha."""
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
        """Actualiza una cotización existente.

        Raises:
            ValueError: Si no se encuentra la cotización.
        """
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
        """Elimina la cotización de un tipo y fecha. True si existía."""
        with self._conexion.transaccion() as sesion:
            modelo = self._buscar(sesion, tipo_id, fecha)
            if modelo is None:
                return False
            sesion.delete(modelo)
            return True
