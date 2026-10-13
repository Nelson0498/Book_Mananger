"""
Servicios: lógica de negocio aplicada sobre las entidades del sistema.

Los repositorios (repositories.py) solo saben leer y escribir; acá se
validan las reglas de negocio y se orquestan las operaciones que
involucran a más de una entidad (por ejemplo, crear un Libro implica
crear también su Stock y su Precio asociados).
"""

import datetime
from typing import List, Optional

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
    RepositorioTipoCotizacion,
)


# ---------------------------------------------------------------------------
# Excepciones de servicio
# ---------------------------------------------------------------------------

class ErrorServicio(Exception):
    """Excepción base para errores de lógica de negocio."""


class EntidadNoEncontradaError(ErrorServicio):
    """Se lanza cuando una operación referencia una entidad inexistente."""


class OperacionInvalidaError(ErrorServicio):
    """Se lanza cuando una operación viola una regla de negocio."""


# ---------------------------------------------------------------------------
# ServicioGenero
# ---------------------------------------------------------------------------

class ServicioGenero:
    """Lógica de negocio para Genero."""

    def __init__(self, repositorio_genero: RepositorioGenero,
                 repositorio_libro: RepositorioLibro) -> None:
        self._repositorio_genero = repositorio_genero
        self._repositorio_libro = repositorio_libro

    def crear(self, id_genero: int, nombre: str) -> Genero:
        if any(g.nombre.lower() == nombre.lower()
               for g in self._repositorio_genero.leer_todos()):
            raise OperacionInvalidaError(
                f"Ya existe un género llamado '{nombre}'"
            )
        return self._repositorio_genero.crear(
            Genero(id_genero=id_genero, nombre=nombre)
        )

    def obtener(self, id_genero: int) -> Genero:
        genero = self._repositorio_genero.leer_por_id(id_genero)
        if genero is None:
            raise EntidadNoEncontradaError(
                f"No existe el género con id {id_genero}"
            )
        return genero

    def listar(self) -> List[Genero]:
        return self._repositorio_genero.leer_todos()

    def actualizar_nombre(self, id_genero: int,
                          nuevo_nombre: str) -> Genero:
        genero = self.obtener(id_genero)
        genero.nombre = nuevo_nombre
        return self._repositorio_genero.actualizar(genero)

    def eliminar(self, id_genero: int) -> bool:
        self.obtener(id_genero)
        en_uso = any(
            libro.genero.id_genero == id_genero
            for libro in self._repositorio_libro.leer_todos()
        )
        if en_uso:
            raise OperacionInvalidaError(
                "No se puede eliminar un género con libros asociados"
            )
        return self._repositorio_genero.eliminar(id_genero)


# ---------------------------------------------------------------------------
# ServicioEditorial
# ---------------------------------------------------------------------------

class ServicioEditorial:
    """Lógica de negocio para Editorial."""

    def __init__(self, repositorio_editorial: RepositorioEditorial,
                 repositorio_libro: RepositorioLibro) -> None:
        self._repositorio_editorial = repositorio_editorial
        self._repositorio_libro = repositorio_libro

    def crear(self, id_editorial: int, nombre: str,
              pais: Optional[str] = None) -> Editorial:
        if any(e.nombre.lower() == nombre.lower()
               for e in self._repositorio_editorial.leer_todos()):
            raise OperacionInvalidaError(
                f"Ya existe una editorial llamada '{nombre}'"
            )
        return self._repositorio_editorial.crear(
            Editorial(
                id_editorial=id_editorial, nombre=nombre, pais=pais
            )
        )

    def obtener(self, id_editorial: int) -> Editorial:
        editorial = self._repositorio_editorial.leer_por_id(id_editorial)
        if editorial is None:
            raise EntidadNoEncontradaError(
                f"No existe la editorial con id {id_editorial}"
            )
        return editorial

    def listar(self) -> List[Editorial]:
        return self._repositorio_editorial.leer_todos()

    def actualizar(self, id_editorial: int,
                   nombre: Optional[str] = None,
                   pais: Optional[str] = None) -> Editorial:
        editorial = self.obtener(id_editorial)
        if nombre is not None:
            editorial.nombre = nombre
        if pais is not None:
            editorial.pais = pais
        return self._repositorio_editorial.actualizar(editorial)

    def eliminar(self, id_editorial: int) -> bool:
        self.obtener(id_editorial)
        en_uso = any(
            libro.editorial.id_editorial == id_editorial
            for libro in self._repositorio_libro.leer_todos()
        )
        if en_uso:
            raise OperacionInvalidaError(
                "No se puede eliminar una editorial con libros asociados"
            )
        return self._repositorio_editorial.eliminar(id_editorial)


# ---------------------------------------------------------------------------
# ServicioMoneda
# ---------------------------------------------------------------------------

class ServicioMoneda:
    """Lógica de negocio para Moneda."""

    def __init__(self, repositorio_moneda: RepositorioMoneda,
                 repositorio_precio: RepositorioPrecio) -> None:
        self._repositorio_moneda = repositorio_moneda
        self._repositorio_precio = repositorio_precio

    def crear(self, id_moneda: int, codigo: str, nombre: str,
              simbolo: str) -> Moneda:
        if any(m.codigo == codigo.upper()
               for m in self._repositorio_moneda.leer_todos()):
            raise OperacionInvalidaError(
                f"Ya existe una moneda con código {codigo.upper()}"
            )
        return self._repositorio_moneda.crear(
            Moneda(
                id_moneda=id_moneda, codigo=codigo,
                nombre=nombre, simbolo=simbolo,
            )
        )

    def obtener(self, id_moneda: int) -> Moneda:
        moneda = self._repositorio_moneda.leer_por_id(id_moneda)
        if moneda is None:
            raise EntidadNoEncontradaError(
                f"No existe la moneda con id {id_moneda}"
            )
        return moneda

    def obtener_por_codigo(self, codigo: str) -> Moneda:
        for moneda in self._repositorio_moneda.leer_todos():
            if moneda.codigo == codigo.upper():
                return moneda
        raise EntidadNoEncontradaError(
            f"No existe la moneda con código {codigo.upper()}"
        )

    def listar(self) -> List[Moneda]:
        return self._repositorio_moneda.leer_todos()

    def actualizar(self, id_moneda: int,
                   nombre: Optional[str] = None,
                   simbolo: Optional[str] = None) -> Moneda:
        moneda = self.obtener(id_moneda)
        if nombre is not None:
            moneda.nombre = nombre
        if simbolo is not None:
            moneda.simbolo = simbolo
        return self._repositorio_moneda.actualizar(moneda)

    def eliminar(self, id_moneda: int) -> bool:
        self.obtener(id_moneda)
        en_uso = any(
            precio.moneda.id_moneda == id_moneda
            for precio in self._repositorio_precio.leer_todos()
        )
        if en_uso:
            raise OperacionInvalidaError(
                "No se puede eliminar una moneda utilizada por precios"
            )
        return self._repositorio_moneda.eliminar(id_moneda)


# ---------------------------------------------------------------------------
# ServicioTipoCotizacion
# ---------------------------------------------------------------------------

class ServicioTipoCotizacion:
    """Lógica de negocio para TipoCotizacion."""

    def __init__(
        self,
        repositorio_tipo_cotizacion: RepositorioTipoCotizacion,
        repositorio_cotizacion: RepositorioCotizacionDolar,
    ) -> None:
        self._repositorio_tipo_cotizacion = repositorio_tipo_cotizacion
        self._repositorio_cotizacion = repositorio_cotizacion

    def crear(self, id_tipo: int, nombre: str) -> TipoCotizacion:
        if any(t.nombre.lower() == nombre.lower()
               for t in self._repositorio_tipo_cotizacion.leer_todos()):
            raise OperacionInvalidaError(
                f"Ya existe un tipo de cotización llamado '{nombre}'"
            )
        return self._repositorio_tipo_cotizacion.crear(
            TipoCotizacion(id_tipo=id_tipo, nombre=nombre)
        )

    def obtener(self, id_tipo: int) -> TipoCotizacion:
        tipo = self._repositorio_tipo_cotizacion.leer_por_id(id_tipo)
        if tipo is None:
            raise EntidadNoEncontradaError(
                f"No existe el tipo de cotización con id {id_tipo}"
            )
        return tipo

    def listar(self) -> List[TipoCotizacion]:
        return self._repositorio_tipo_cotizacion.leer_todos()

    def actualizar_nombre(self, id_tipo: int,
                          nuevo_nombre: str) -> TipoCotizacion:
        tipo = self.obtener(id_tipo)
        tipo.nombre = nuevo_nombre
        return self._repositorio_tipo_cotizacion.actualizar(tipo)

    def eliminar(self, id_tipo: int) -> bool:
        self.obtener(id_tipo)
        en_uso = any(
            cotizacion.tipo.id_tipo == id_tipo
            for cotizacion in self._repositorio_cotizacion.leer_todos()
        )
        if en_uso:
            raise OperacionInvalidaError(
                "No se puede eliminar un tipo de cotización "
                "con cotizaciones asociadas"
            )
        return self._repositorio_tipo_cotizacion.eliminar(id_tipo)


# ---------------------------------------------------------------------------
# ServicioPrecio
# ---------------------------------------------------------------------------

class ServicioPrecio:
    """Lógica de negocio para Precio."""

    def __init__(self, repositorio_precio: RepositorioPrecio,
                 repositorio_moneda: RepositorioMoneda) -> None:
        self._repositorio_precio = repositorio_precio
        self._repositorio_moneda = repositorio_moneda

    def crear(self, id_precio: int, valor: float,
              moneda_id: int) -> Precio:
        moneda = self._repositorio_moneda.leer_por_id(moneda_id)
        if moneda is None:
            raise EntidadNoEncontradaError(
                f"No existe la moneda con id {moneda_id}"
            )
        return self._repositorio_precio.crear(
            Precio(id_precio=id_precio, valor=valor, moneda=moneda)
        )

    def obtener(self, id_precio: int) -> Precio:
        precio = self._repositorio_precio.leer_por_id(id_precio)
        if precio is None:
            raise EntidadNoEncontradaError(
                f"No existe el precio con id {id_precio}"
            )
        return precio

    def listar(self) -> List[Precio]:
        return self._repositorio_precio.leer_todos()

    def actualizar(self, id_precio: int,
                   nuevo_valor: Optional[float] = None) -> Precio:
        precio = self.obtener(id_precio)
        if nuevo_valor is not None:
            precio.valor = nuevo_valor
        return self._repositorio_precio.actualizar(precio)

    def eliminar(self, id_precio: int) -> bool:
        self.obtener(id_precio)
        return self._repositorio_precio.eliminar(id_precio)


# ---------------------------------------------------------------------------
# ServicioCotizacionDolar
# ---------------------------------------------------------------------------

class ServicioCotizacionDolar:
    """Lógica de negocio para CotizacionDolar."""

    def __init__(
        self,
        repositorio_cotizacion: RepositorioCotizacionDolar,
        repositorio_tipo_cotizacion: RepositorioTipoCotizacion,
    ) -> None:
        self._repositorio_cotizacion = repositorio_cotizacion
        self._repositorio_tipo_cotizacion = repositorio_tipo_cotizacion

    def registrar(
        self, id_cotizacion: int, tipo_id: int,
        valor_compra: float, valor_venta: float,
        fecha: Optional[datetime.date] = None,
    ) -> CotizacionDolar:
        tipo = self._repositorio_tipo_cotizacion.leer_por_id(tipo_id)
        if tipo is None:
            raise EntidadNoEncontradaError(
                f"No existe el tipo de cotización con id {tipo_id}"
            )
        if valor_compra > valor_venta:
            raise OperacionInvalidaError(
                "El valor de compra no puede ser mayor al de venta"
            )
        cotizacion = CotizacionDolar(
            id_cotizacion=id_cotizacion, tipo=tipo,
            valor_compra=valor_compra, valor_venta=valor_venta,
            fecha=fecha,
        )
        return self._repositorio_cotizacion.crear(cotizacion)

    def obtener_vigente(self, tipo_id: int) -> CotizacionDolar:
        """Devuelve la cotización más reciente registrada para un tipo."""
        historico = self._repositorio_cotizacion.leer_historico_por_tipo(
            tipo_id
        )
        if not historico:
            raise EntidadNoEncontradaError(
                f"No hay cotizaciones registradas para el tipo {tipo_id}"
            )
        return max(historico, key=lambda c: c.fecha)

    def historico(self, tipo_id: int) -> List[CotizacionDolar]:
        return self._repositorio_cotizacion.leer_historico_por_tipo(
            tipo_id
        )

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        if cotizacion.valor_compra > cotizacion.valor_venta:
            raise OperacionInvalidaError(
                "El valor de compra no puede ser mayor al de venta"
            )
        return self._repositorio_cotizacion.actualizar(cotizacion)

    def eliminar(self, tipo_id: int,
                 fecha: datetime.date) -> bool:
        return self._repositorio_cotizacion.eliminar(tipo_id, fecha)


# ---------------------------------------------------------------------------
# ServicioStock
# ---------------------------------------------------------------------------

class ServicioStock:
    """Lógica de negocio para Stock: ingresos, egresos y alertas."""

    def __init__(self, repositorio_stock: RepositorioStock) -> None:
        self._repositorio_stock = repositorio_stock

    def crear(self, id_stock: int, libro_isbn: str,
              cantidad: int = 0,
              cantidad_minima: int = 0) -> Stock:
        """Crea un registro de stock para un libro."""
        return self._repositorio_stock.crear(
            Stock(
                id_stock=id_stock, cantidad=cantidad,
                cantidad_minima=cantidad_minima, libro_isbn=libro_isbn,
            )
        )

    def obtener(self, isbn: str) -> Stock:
        stock = self._repositorio_stock.leer_por_libro(isbn)
        if stock is None:
            raise EntidadNoEncontradaError(
                f"No hay stock registrado para el libro {isbn}"
            )
        return stock

    def listar(self) -> List[Stock]:
        """Devuelve todos los registros de stock."""
        return self._repositorio_stock.leer_todos()

    def registrar_ingreso(self, isbn: str, cantidad: int) -> Stock:
        if cantidad <= 0:
            raise OperacionInvalidaError(
                "La cantidad a ingresar debe ser positiva"
            )
        stock = self.obtener(isbn)
        stock.cantidad += cantidad
        return self._repositorio_stock.actualizar(stock)

    def registrar_egreso(self, isbn: str, cantidad: int) -> Stock:
        if cantidad <= 0:
            raise OperacionInvalidaError(
                "La cantidad a retirar debe ser positiva"
            )
        stock = self.obtener(isbn)
        if cantidad > stock.cantidad:
            raise OperacionInvalidaError(
                f"No hay stock suficiente para el libro {isbn} "
                f"(disponible: {stock.cantidad}, "
                f"solicitado: {cantidad})"
            )
        stock.cantidad -= cantidad
        return self._repositorio_stock.actualizar(stock)

    def eliminar(self, isbn: str) -> bool:
        """Elimina el registro de stock de un libro."""
        return self._repositorio_stock.eliminar(isbn)

    def hay_alerta_stock_bajo(self, isbn: str) -> bool:
        return self.obtener(isbn).hay_stock_bajo()


# ---------------------------------------------------------------------------
# ServicioLibro
# ---------------------------------------------------------------------------

class ServicioLibro:
    """Lógica de negocio para Libro: crea/actualiza el libro junto con su
    Precio y su Stock, y valida las relaciones con Genero, Editorial y
    Moneda.
    """

    def __init__(
        self,
        repositorio_libro: RepositorioLibro,
        repositorio_genero: RepositorioGenero,
        repositorio_editorial: RepositorioEditorial,
        repositorio_moneda: RepositorioMoneda,
        repositorio_precio: RepositorioPrecio,
        repositorio_stock: RepositorioStock,
    ) -> None:
        self._repositorio_libro = repositorio_libro
        self._repositorio_genero = repositorio_genero
        self._repositorio_editorial = repositorio_editorial
        self._repositorio_moneda = repositorio_moneda
        self._repositorio_precio = repositorio_precio
        self._repositorio_stock = repositorio_stock

    def crear(
        self, isbn: str, titulo: str, autor: str,
        editorial_id: int, genero_id: int,
        precio_id: int, precio_valor: float, moneda_id: int,
        stock_id: int, cantidad_inicial: int = 0,
        cantidad_minima: int = 0,
    ) -> Libro:
        """Crea un libro con su precio y stock asociados.

        Flujo:
        1. Verificar que no exista el ISBN.
        2. Verificar que existan género, editorial y moneda.
        3. Crear el precio.
        4. Crear el stock.
        5. Crear el libro.
        """
        if self._repositorio_libro.leer_por_isbn(isbn) is not None:
            raise OperacionInvalidaError(
                f"Ya existe un libro con ISBN {isbn}"
            )

        genero = self._repositorio_genero.leer_por_id(genero_id)
        if genero is None:
            raise EntidadNoEncontradaError(
                f"No existe el género con id {genero_id}"
            )

        editorial = self._repositorio_editorial.leer_por_id(editorial_id)
        if editorial is None:
            raise EntidadNoEncontradaError(
                f"No existe la editorial con id {editorial_id}"
            )

        moneda = self._repositorio_moneda.leer_por_id(moneda_id)
        if moneda is None:
            raise EntidadNoEncontradaError(
                f"No existe la moneda con id {moneda_id}"
            )

        precio = Precio(
            id_precio=precio_id, valor=precio_valor, moneda=moneda
        )
        self._repositorio_precio.crear(precio)

        stock = Stock(
            id_stock=stock_id, cantidad=cantidad_inicial,
            cantidad_minima=cantidad_minima, libro_isbn=isbn,
        )
        self._repositorio_stock.crear(stock)

        libro = Libro(
            isbn=isbn, titulo=titulo, autor=autor,
            editorial=editorial, genero=genero,
            precio=precio, stock=stock,
        )
        return self._repositorio_libro.crear(libro)

    def obtener(self, isbn: str) -> Libro:
        libro = self._repositorio_libro.leer_por_isbn(isbn)
        if libro is None:
            raise EntidadNoEncontradaError(
                f"No existe el libro con ISBN {isbn}"
            )
        return libro

    def listar(self) -> List[Libro]:
        return self._repositorio_libro.leer_todos()

    def actualizar_datos(self, isbn: str,
                         titulo: Optional[str] = None,
                         autor: Optional[str] = None) -> Libro:
        libro = self.obtener(isbn)
        if titulo is not None:
            libro.titulo = titulo
        if autor is not None:
            libro.autor = autor
        return self._repositorio_libro.actualizar(libro)

    def actualizar_precio(self, isbn: str,
                          nuevo_valor: float) -> Libro:
        """Actualiza el valor del precio asociado al libro."""
        libro = self.obtener(isbn)
        libro.precio.valor = nuevo_valor
        self._repositorio_precio.actualizar(libro.precio)
        return libro

    def eliminar(self, isbn: str) -> bool:
        """Elimina un libro junto con su stock y precio asociados.

        Flujo:
        1. Verificar que el libro existe.
        2. Eliminar el stock asociado.
        3. Eliminar el precio asociado.
        4. Eliminar el libro.
        """
        libro = self.obtener(isbn)
        self._repositorio_stock.eliminar(isbn)
        self._repositorio_precio.eliminar(libro.precio.id_precio)
        return self._repositorio_libro.eliminar(isbn)

    def cotizar_en(self, isbn: str,
                   cotizacion: CotizacionDolar) -> float:
        """Convierte el precio del libro usando una cotización del dólar.

        Si el precio está en USD, lo pasa a ARS con el valor de venta;
        si está en ARS, lo pasa a USD con el valor de compra.  Otras
        monedas no están soportadas por esta operación.
        """
        libro = self.obtener(isbn)
        codigo = libro.precio.moneda.codigo
        if codigo == "USD":
            return round(
                libro.precio.valor * cotizacion.valor_venta, 2
            )
        if codigo == "ARS":
            return round(
                libro.precio.valor / cotizacion.valor_compra, 2
            )
        raise OperacionInvalidaError(
            f"No se sabe cotizar la moneda {codigo}"
        )