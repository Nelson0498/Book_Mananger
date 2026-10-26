"""Servicios: lógica de negocio aplicada sobre las entidades del sistema.

Los repositorios (repositories.py) solo saben leer y escribir; acá se
validan las reglas de negocio y se orquestan las operaciones que
involucran a más de una entidad (por ejemplo, crear un Libro implica
crear también sus Precios y su Stock asociados).
"""

import csv
import datetime
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

import pandas as pd
from openpyxl.utils import get_column_letter

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Libro,
    Moneda,
    Precio,
    PrecioWeb,
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
    RepositorioPrecioWeb,
    RepositorioStock,
    RepositorioTipoCotizacion,
)

# Carpeta del paquete `book_manager` y carpeta `src` que la contiene.
_CARPETA_PAQUETE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CARPETA_SRC = os.path.dirname(_CARPETA_PAQUETE)

# Carpeta del proyecto Scrapy (contiene `scrapy.cfg`).
CARPETA_SCRAPER = os.path.join(_CARPETA_PAQUETE, "scraper")

# Carpeta donde se guardan los reportes generados (CSV y Excel).
CARPETA_REPORTES = os.path.join(_CARPETA_PAQUETE, "reportes")

# Código de la moneda en la que todo libro debe tener precio obligatorio.
MONEDA_BASE = "ARS"


# ---------------------------------------------------------------------------
# Excepciones de servicio
# ---------------------------------------------------------------------------

class ErrorServicio(Exception):
    """Excepción base para errores de lógica de negocio."""


class EntidadNoEncontradaError(ErrorServicio):
    """Se lanza cuando una operación referencia una entidad inexistente."""


class OperacionInvalidaError(ErrorServicio):
    """Se lanza cuando una operación viola una regla de negocio."""


def _siguiente_id(ids: List[int]) -> int:
    """Calcula el próximo identificador a partir de los existentes.

    Los identificadores los administra la aplicación, igual que en el
    Sprint 1, por lo que no se delega en una secuencia de la base de datos.

    Args:
        ids (List[int]): Identificadores ya utilizados.

    Returns:
        int: El mayor identificador más uno, o 1 si no hay ninguno.
    """
    return max(ids, default=0) + 1


# ---------------------------------------------------------------------------
# ServicioGenero
# ---------------------------------------------------------------------------

class ServicioGenero:
    """Lógica de negocio para Genero."""

    def __init__(self, repositorio_genero: RepositorioGenero,
                 repositorio_libro: RepositorioLibro) -> None:
        """Crea el servicio.

        Args:
            repositorio_genero (RepositorioGenero): Repositorio de géneros.
            repositorio_libro (RepositorioLibro): Repositorio de libros.
        """
        self._repositorio_genero = repositorio_genero
        self._repositorio_libro = repositorio_libro

    def crear(self, id_genero: int, nombre: str) -> Genero:
        """Crea un género.

        Args:
            id_genero (int): Identificador del género.
            nombre (str): Nombre del género.

        Returns:
            Genero: El género creado.

        Raises:
            OperacionInvalidaError: Si ya existe un género con ese nombre.
        """
        if any(g.nombre.lower() == nombre.lower()
               for g in self._repositorio_genero.leer_todos()):
            raise OperacionInvalidaError(
                f"Ya existe un género llamado '{nombre}'"
            )
        return self._repositorio_genero.crear(
            Genero(id_genero=id_genero, nombre=nombre)
        )

    def obtener(self, id_genero: int) -> Genero:
        """Devuelve el género con el id dado.

        Raises:
            EntidadNoEncontradaError: Si no existe.
        """
        genero = self._repositorio_genero.leer_por_id(id_genero)
        if genero is None:
            raise EntidadNoEncontradaError(
                f"No existe el género con id {id_genero}"
            )
        return genero

    def listar(self) -> List[Genero]:
        """Devuelve todos los géneros."""
        return self._repositorio_genero.leer_todos()

    def actualizar_nombre(self, id_genero: int,
                          nuevo_nombre: str) -> Genero:
        """Modifica el nombre de un género.

        Args:
            id_genero (int): Identificador del género.
            nuevo_nombre (str): Nuevo nombre.

        Returns:
            Genero: El género actualizado.

        Raises:
            EntidadNoEncontradaError: Si el género no existe.
        """
        genero = self.obtener(id_genero)
        genero.nombre = nuevo_nombre
        return self._repositorio_genero.actualizar(genero)

    def eliminar(self, id_genero: int) -> bool:
        """Elimina un género que no tenga libros asociados.

        Raises:
            EntidadNoEncontradaError: Si el género no existe.
            OperacionInvalidaError: Si hay libros que lo usan.
        """
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
        """Crea el servicio.

        Args:
            repositorio_editorial (RepositorioEditorial): Repositorio de
                editoriales.
            repositorio_libro (RepositorioLibro): Repositorio de libros.
        """
        self._repositorio_editorial = repositorio_editorial
        self._repositorio_libro = repositorio_libro

    def crear(self, id_editorial: int, nombre: str,
              pais: Optional[str] = None) -> Editorial:
        """Crea una editorial.

        Args:
            id_editorial (int): Identificador de la editorial.
            nombre (str): Nombre de la editorial.
            pais (Optional[str]): País de origen.

        Returns:
            Editorial: La editorial creada.

        Raises:
            OperacionInvalidaError: Si ya existe una con ese nombre.
        """
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
        """Devuelve la editorial con el id dado.

        Raises:
            EntidadNoEncontradaError: Si no existe.
        """
        editorial = self._repositorio_editorial.leer_por_id(id_editorial)
        if editorial is None:
            raise EntidadNoEncontradaError(
                f"No existe la editorial con id {id_editorial}"
            )
        return editorial

    def listar(self) -> List[Editorial]:
        """Devuelve todas las editoriales."""
        return self._repositorio_editorial.leer_todos()

    def actualizar(self, id_editorial: int,
                   nombre: Optional[str] = None,
                   pais: Optional[str] = None) -> Editorial:
        """Modifica el nombre y/o el país de una editorial.

        Args:
            id_editorial (int): Identificador de la editorial.
            nombre (Optional[str]): Nuevo nombre; None para no cambiarlo.
            pais (Optional[str]): Nuevo país; None para no cambiarlo.

        Returns:
            Editorial: La editorial actualizada.
        """
        editorial = self.obtener(id_editorial)
        if nombre is not None:
            editorial.nombre = nombre
        if pais is not None:
            editorial.pais = pais
        return self._repositorio_editorial.actualizar(editorial)

    def eliminar(self, id_editorial: int) -> bool:
        """Elimina una editorial que no tenga libros asociados.

        Raises:
            EntidadNoEncontradaError: Si la editorial no existe.
            OperacionInvalidaError: Si hay libros que la usan.
        """
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
        """Crea el servicio.

        Args:
            repositorio_moneda (RepositorioMoneda): Repositorio de monedas.
            repositorio_precio (RepositorioPrecio): Repositorio de precios.
        """
        self._repositorio_moneda = repositorio_moneda
        self._repositorio_precio = repositorio_precio

    def crear(self, id_moneda: int, codigo: str, nombre: str,
              simbolo: str) -> Moneda:
        """Crea una moneda.

        Args:
            id_moneda (int): Identificador de la moneda.
            codigo (str): Código de la moneda.
            nombre (str): Nombre de la moneda.
            simbolo (str): Símbolo de la moneda.

        Returns:
            Moneda: La moneda creada.

        Raises:
            OperacionInvalidaError: Si ya existe una con ese código.
        """
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
        """Devuelve la moneda con el id dado.

        Raises:
            EntidadNoEncontradaError: Si no existe.
        """
        moneda = self._repositorio_moneda.leer_por_id(id_moneda)
        if moneda is None:
            raise EntidadNoEncontradaError(
                f"No existe la moneda con id {id_moneda}"
            )
        return moneda

    def obtener_por_codigo(self, codigo: str) -> Moneda:
        """Devuelve la moneda con el código dado.

        Raises:
            EntidadNoEncontradaError: Si no existe.
        """
        for moneda in self._repositorio_moneda.leer_todos():
            if moneda.codigo == codigo.upper():
                return moneda
        raise EntidadNoEncontradaError(
            f"No existe la moneda con código {codigo.upper()}"
        )

    def listar(self) -> List[Moneda]:
        """Devuelve todas las monedas."""
        return self._repositorio_moneda.leer_todos()

    def actualizar(self, id_moneda: int,
                   nombre: Optional[str] = None,
                   simbolo: Optional[str] = None) -> Moneda:
        """Modifica el nombre y/o el símbolo de una moneda.

        Args:
            id_moneda (int): Identificador de la moneda.
            nombre (Optional[str]): Nuevo nombre; None para no cambiarlo.
            simbolo (Optional[str]): Nuevo símbolo; None para no cambiarlo.

        Returns:
            Moneda: La moneda actualizada.
        """
        moneda = self.obtener(id_moneda)
        if nombre is not None:
            moneda.nombre = nombre
        if simbolo is not None:
            moneda.simbolo = simbolo
        return self._repositorio_moneda.actualizar(moneda)

    def eliminar(self, id_moneda: int) -> bool:
        """Elimina una moneda que no esté usada por ningún precio.

        Raises:
            EntidadNoEncontradaError: Si la moneda no existe.
            OperacionInvalidaError: Si hay precios que la usan.
        """
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
        """Crea el servicio.

        Args:
            repositorio_tipo_cotizacion (RepositorioTipoCotizacion):
                Repositorio de tipos de cotización.
            repositorio_cotizacion (RepositorioCotizacionDolar):
                Repositorio de cotizaciones.
        """
        self._repositorio_tipo_cotizacion = repositorio_tipo_cotizacion
        self._repositorio_cotizacion = repositorio_cotizacion

    def crear(self, id_tipo: int, nombre: str) -> TipoCotizacion:
        """Crea un tipo de cotización.

        Args:
            id_tipo (int): Identificador del tipo.
            nombre (str): Nombre del tipo.

        Returns:
            TipoCotizacion: El tipo creado.

        Raises:
            OperacionInvalidaError: Si ya existe uno con ese nombre.
        """
        if any(t.nombre.lower() == nombre.lower()
               for t in self._repositorio_tipo_cotizacion.leer_todos()):
            raise OperacionInvalidaError(
                f"Ya existe un tipo de cotización llamado '{nombre}'"
            )
        return self._repositorio_tipo_cotizacion.crear(
            TipoCotizacion(id_tipo=id_tipo, nombre=nombre)
        )

    def obtener(self, id_tipo: int) -> TipoCotizacion:
        """Devuelve el tipo de cotización con el id dado.

        Raises:
            EntidadNoEncontradaError: Si no existe.
        """
        tipo = self._repositorio_tipo_cotizacion.leer_por_id(id_tipo)
        if tipo is None:
            raise EntidadNoEncontradaError(
                f"No existe el tipo de cotización con id {id_tipo}"
            )
        return tipo

    def listar(self) -> List[TipoCotizacion]:
        """Devuelve todos los tipos de cotización."""
        return self._repositorio_tipo_cotizacion.leer_todos()

    def actualizar_nombre(self, id_tipo: int,
                          nuevo_nombre: str) -> TipoCotizacion:
        """Modifica el nombre de un tipo de cotización.

        Args:
            id_tipo (int): Identificador del tipo.
            nuevo_nombre (str): Nuevo nombre.

        Returns:
            TipoCotizacion: El tipo actualizado.
        """
        tipo = self.obtener(id_tipo)
        tipo.nombre = nuevo_nombre
        return self._repositorio_tipo_cotizacion.actualizar(tipo)

    def eliminar(self, id_tipo: int) -> bool:
        """Elimina un tipo que no tenga cotizaciones asociadas.

        Raises:
            EntidadNoEncontradaError: Si el tipo no existe.
            OperacionInvalidaError: Si tiene cotizaciones asociadas.
        """
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
    """Lógica de negocio para Precio: un precio por moneda y por libro."""

    def __init__(self, repositorio_precio: RepositorioPrecio,
                 repositorio_moneda: RepositorioMoneda,
                 repositorio_libro: RepositorioLibro) -> None:
        """Crea el servicio.

        Args:
            repositorio_precio (RepositorioPrecio): Repositorio de precios.
            repositorio_moneda (RepositorioMoneda): Repositorio de monedas.
            repositorio_libro (RepositorioLibro): Repositorio de libros.
        """
        self._repositorio_precio = repositorio_precio
        self._repositorio_moneda = repositorio_moneda
        self._repositorio_libro = repositorio_libro

    def agregar(self, libro_id: int, codigo_moneda: str,
                valor: float) -> Precio:
        """Agrega a un libro un precio en una moneda.

        Args:
            libro_id (int): Identificador del libro.
            codigo_moneda (str): Código de la moneda del precio.
            valor (float): Importe, no negativo.

        Returns:
            Precio: El precio creado.

        Raises:
            EntidadNoEncontradaError: Si el libro o la moneda no existen.
            OperacionInvalidaError: Si el libro ya tiene precio en esa
                moneda.
        """
        libro = self._repositorio_libro.leer_por_id(libro_id)
        if libro is None:
            raise EntidadNoEncontradaError(
                f"No existe el libro con id {libro_id}"
            )
        moneda = next(
            (m for m in self._repositorio_moneda.leer_todos()
             if m.codigo == codigo_moneda.upper()),
            None,
        )
        if moneda is None:
            raise EntidadNoEncontradaError(
                f"No existe la moneda con código {codigo_moneda.upper()}"
            )
        if libro.precio_en(moneda.codigo) is not None:
            raise OperacionInvalidaError(
                f"El libro {libro_id} ya tiene un precio en {moneda.codigo}"
            )

        id_precio = _siguiente_id(
            [p.id_precio for p in self._repositorio_precio.leer_todos()]
        )
        precio = Precio(id_precio=id_precio, valor=valor, moneda=moneda)
        libro.agregar_precio(precio)
        return self._repositorio_precio.crear(precio)

    def obtener(self, id_precio: int) -> Precio:
        """Devuelve el precio con el id dado.

        Raises:
            EntidadNoEncontradaError: Si no existe.
        """
        precio = self._repositorio_precio.leer_por_id(id_precio)
        if precio is None:
            raise EntidadNoEncontradaError(
                f"No existe el precio con id {id_precio}"
            )
        return precio

    def listar(self) -> List[Precio]:
        """Devuelve todos los precios."""
        return self._repositorio_precio.leer_todos()

    def listar_por_libro(self, libro_id: int) -> List[Precio]:
        """Devuelve los precios de un libro, uno por moneda.

        Raises:
            EntidadNoEncontradaError: Si el libro no existe.
        """
        if self._repositorio_libro.leer_por_id(libro_id) is None:
            raise EntidadNoEncontradaError(
                f"No existe el libro con id {libro_id}"
            )
        return self._repositorio_precio.leer_por_libro(libro_id)

    def actualizar(self, id_precio: int,
                   nuevo_valor: Optional[float] = None) -> Precio:
        """Modifica el importe de un precio.

        Args:
            id_precio (int): Identificador del precio.
            nuevo_valor (Optional[float]): Nuevo importe; None para no
                cambiarlo.

        Returns:
            Precio: El precio actualizado.
        """
        precio = self.obtener(id_precio)
        if nuevo_valor is not None:
            precio.valor = nuevo_valor
        return self._repositorio_precio.actualizar(precio)

    def eliminar(self, id_precio: int) -> bool:
        """Elimina un precio, salvo que sea el precio en pesos del libro.

        Raises:
            EntidadNoEncontradaError: Si el precio no existe.
            OperacionInvalidaError: Si es el precio ARS del libro, que es
                obligatorio.
        """
        precio = self.obtener(id_precio)
        if precio.moneda.codigo == MONEDA_BASE:
            raise OperacionInvalidaError(
                f"No se puede eliminar el precio en {MONEDA_BASE}: todo "
                f"libro debe tener precio en pesos"
            )
        return self._repositorio_precio.eliminar(id_precio)


# ---------------------------------------------------------------------------
# ServicioCotizacionDolar
# ---------------------------------------------------------------------------

# Correspondencia entre las casas que informa la API del dólar y los tipos de
# cotización registrados en el sistema. Los nombres no coinciden literalmente:
# la casa `bolsa` es el tipo MEP y `contadoconliqui` es el CCL.
MAPA_CASAS_API: Dict[str, str] = {
    "oficial": "Oficial",
    "blue": "Blue",
    "bolsa": "MEP",
    "contadoconliqui": "CCL",
    "mayorista": "Mayorista",
    "cripto": "Cripto",
    "tarjeta": "Tarjeta",
}

# Tipo de cotización que se usa por defecto para convertir pesos y dólares.
TIPO_COTIZACION_OFICIAL = "Oficial"

# Identificación del cliente y espera máxima al consultar la API.
USER_AGENT_API = "BookManager/3.0 (Trabajo Practico Integrador; urllib)"
ESPERA_API_SEGUNDOS = 10


def _descargar_cotizaciones(url: str) -> List[Dict[str, Any]]:
    """Descarga la lista de cotizaciones desde la API configurada.

    Args:
        url (str): Endpoint de la API de cotizaciones.

    Returns:
        List[Dict[str, Any]]: Registros devueltos por la API.

    Raises:
        urllib.error.URLError: Si no se puede contactar la API.
        ValueError: Si la respuesta no es una lista de cotizaciones.
    """
    peticion = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT_API, "Accept": "application/json"},
    )

    with urllib.request.urlopen(
        peticion, timeout=ESPERA_API_SEGUNDOS
    ) as respuesta:
        contenido = respuesta.read().decode("utf-8")

    datos = json.loads(contenido)

    if not isinstance(datos, list):
        raise ValueError("La API no devolvió una lista de cotizaciones")

    return datos


def _fecha_desde_api(valor: Optional[str]) -> datetime.date:
    """Extrae la fecha del campo `fechaActualizacion` de la API.

    La API informa la marca de tiempo en UTC, por lo que se toma esa misma
    fecha para que el resultado no dependa de la zona horaria del equipo.

    Args:
        valor (Optional[str]): Marca de tiempo ISO 8601 informada por la API.

    Returns:
        datetime.date: Fecha de la cotización, o la fecha actual si la API no
        informa el campo.
    """
    if not valor:
        return datetime.date.today()

    return datetime.datetime.fromisoformat(valor.replace("Z", "+00:00")).date()


class ServicioCotizacionDolar:
    """Lógica de negocio para CotizacionDolar."""

    def __init__(
        self,
        repositorio_cotizacion: RepositorioCotizacionDolar,
        repositorio_tipo_cotizacion: RepositorioTipoCotizacion,
    ) -> None:
        """Crea el servicio.

        Args:
            repositorio_cotizacion (RepositorioCotizacionDolar): Repositorio
                de cotizaciones.
            repositorio_tipo_cotizacion (RepositorioTipoCotizacion):
                Repositorio de tipos de cotización.
        """
        self._repositorio_cotizacion = repositorio_cotizacion
        self._repositorio_tipo_cotizacion = repositorio_tipo_cotizacion

    def registrar(
        self, id_cotizacion: int, tipo_id: int,
        valor_compra: float, valor_venta: float,
        fecha: Optional[datetime.date] = None,
    ) -> CotizacionDolar:
        """Registra una cotización del dólar.

        Args:
            id_cotizacion (int): Identificador de la cotización.
            tipo_id (int): Identificador del tipo de cotización.
            valor_compra (float): Valor de compra.
            valor_venta (float): Valor de venta.
            fecha (Optional[datetime.date]): Fecha; por defecto, hoy.

        Returns:
            CotizacionDolar: La cotización registrada.

        Raises:
            EntidadNoEncontradaError: Si el tipo no existe.
            OperacionInvalidaError: Si la compra supera a la venta.
        """
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
        """Devuelve la cotización más reciente registrada para un tipo.

        Raises:
            EntidadNoEncontradaError: Si el tipo no tiene cotizaciones.
        """
        historico = self._repositorio_cotizacion.leer_historico_por_tipo(
            tipo_id
        )
        if not historico:
            raise EntidadNoEncontradaError(
                f"No hay cotizaciones registradas para el tipo {tipo_id}"
            )
        return max(historico, key=lambda c: c.fecha)

    def listar_vigentes(self) -> List[CotizacionDolar]:
        """Devuelve la cotización más reciente de cada tipo con datos.

        Returns:
            List[CotizacionDolar]: Una cotización por tipo, ordenadas por
            id de tipo.
        """
        ultimas: Dict[int, CotizacionDolar] = {}
        for cotizacion in self._repositorio_cotizacion.leer_todos():
            actual = ultimas.get(cotizacion.tipo.id_tipo)
            if actual is None or cotizacion.fecha > actual.fecha:
                ultimas[cotizacion.tipo.id_tipo] = cotizacion
        return [ultimas[clave] for clave in sorted(ultimas)]

    def historico(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve el histórico de cotizaciones de un tipo."""
        return self._repositorio_cotizacion.leer_historico_por_tipo(
            tipo_id
        )

    def obtener_vigente_por_nombre(self, nombre: str) -> CotizacionDolar:
        """Devuelve la cotización vigente del tipo indicado por su nombre.

        Args:
            nombre (str): Nombre del tipo de cotización (por ejemplo, Oficial).

        Returns:
            CotizacionDolar: La cotización más reciente de ese tipo.

        Raises:
            EntidadNoEncontradaError: Si no existe el tipo de cotización.
        """
        for tipo in self._repositorio_tipo_cotizacion.leer_todos():
            if tipo.nombre.strip().lower() == nombre.strip().lower():
                return self.obtener_vigente(tipo.id_tipo)

        raise EntidadNoEncontradaError(
            f"No existe el tipo de cotización '{nombre}'"
        )

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Actualiza una cotización existente.

        Raises:
            OperacionInvalidaError: Si la compra supera a la venta.
        """
        if cotizacion.valor_compra > cotizacion.valor_venta:
            raise OperacionInvalidaError(
                "El valor de compra no puede ser mayor al de venta"
            )
        return self._repositorio_cotizacion.actualizar(cotizacion)

    def eliminar(self, tipo_id: int,
                 fecha: datetime.date) -> bool:
        """Elimina la cotización de un tipo y fecha. True si existía."""
        return self._repositorio_cotizacion.eliminar(tipo_id, fecha)

    def obtener_cotizaciones(self) -> List[CotizacionDolar]:
        """Consulta la API del dólar y registra las cotizaciones del día.

        Los tipos que ya tienen una cotización para la fecha informada se
        actualizan en lugar de duplicarse, de modo que la operación puede
        repetirse sin generar registros repetidos. Si la API informa una casa
        cuyo tipo todavía no existe en el sistema, el tipo se crea: con el
        nombre de `MAPA_CASAS_API` si la casa es conocida o con la casa
        capitalizada si no lo es. Las casas sin valores de compra y venta no
        se registran: no se inventan cotizaciones.

        Returns:
            List[CotizacionDolar]: Cotizaciones registradas o actualizadas.

        Raises:
            OperacionInvalidaError: Si no está configurada la variable
                API_URL.
            ErrorServicio: Si la API no responde o devuelve datos inválidos.
        """
        url = os.getenv("API_URL")
        if not url:
            raise OperacionInvalidaError(
                "No se encontró API_URL. Revisá el archivo .env."
            )

        datos = self._consultar_api(url)

        tipos = self._repositorio_tipo_cotizacion.leer_todos()
        tipos_por_nombre = {
            tipo.nombre.strip().lower(): tipo for tipo in tipos
        }
        proximo_id_tipo = _siguiente_id([tipo.id_tipo for tipo in tipos])

        # Primero se resuelven todos los registros y recién después se
        # registran las cotizaciones.
        resueltos = []
        for registro in datos:
            if not isinstance(registro, dict):
                continue

            compra = registro.get("compra")
            venta = registro.get("venta")
            if (not isinstance(compra, (int, float))
                    or not isinstance(venta, (int, float))):
                continue

            casa = str(registro.get("casa", "")).strip().lower()
            if not casa:
                continue
            nombre_tipo = MAPA_CASAS_API.get(casa, casa.capitalize())

            tipo = tipos_por_nombre.get(nombre_tipo.lower())
            if tipo is None:
                tipo = self._repositorio_tipo_cotizacion.crear(
                    TipoCotizacion(
                        id_tipo=proximo_id_tipo, nombre=nombre_tipo
                    )
                )
                tipos_por_nombre[nombre_tipo.lower()] = tipo
                proximo_id_tipo += 1

            resueltos.append((
                tipo, float(compra), float(venta),
                _fecha_desde_api(registro.get("fechaActualizacion")),
            ))

        if not resueltos:
            raise ErrorServicio(
                "La API no devolvió cotizaciones reconocidas para el sistema"
            )

        resultado: List[CotizacionDolar] = []
        for tipo, compra, venta, fecha in resueltos:
            existente = self._repositorio_cotizacion.leer_por_tipo_y_fecha(
                tipo.id_tipo, fecha
            )
            if existente is None:
                resultado.append(
                    self.registrar(
                        self._siguiente_id_cotizacion(), tipo.id_tipo,
                        compra, venta, fecha,
                    )
                )
            else:
                existente.valor_compra = compra
                existente.valor_venta = venta
                resultado.append(self.actualizar(existente))

        return resultado

    def obtener_cotizaciones_monedas(self) -> Dict[str, float]:
        """Consulta la API de cotizaciones de monedas extranjeras.

        Usa el endpoint configurado en `API_URL_MONEDAS`, que informa el valor
        en pesos de cada moneda (USD, EUR, BRL, CLP, UYU, etc.).

        Returns:
            Dict[str, float]: Valor de venta en pesos de cada moneda, por
            código de moneda.

        Raises:
            OperacionInvalidaError: Si no está configurada API_URL_MONEDAS.
            ErrorServicio: Si la API no responde o devuelve datos inválidos.
        """
        url = os.getenv("API_URL_MONEDAS")
        if not url:
            raise OperacionInvalidaError(
                "No se encontró API_URL_MONEDAS. Revisá el archivo .env."
            )

        tasas: Dict[str, float] = {}
        for registro in self._consultar_api(url):
            if not isinstance(registro, dict):
                continue
            codigo = str(registro.get("moneda", "")).strip().upper()
            venta = registro.get("venta")
            if codigo and isinstance(venta, (int, float)) and venta > 0:
                tasas[codigo] = float(venta)

        if not tasas:
            raise ErrorServicio("La API no devolvió cotizaciones de monedas")
        return tasas

    @staticmethod
    def _consultar_api(url: str) -> List[Dict[str, Any]]:
        """Descarga una lista de registros de la API traduciendo errores.

        Raises:
            ErrorServicio: Si la API no responde o devuelve datos inválidos.
        """
        try:
            return _descargar_cotizaciones(url)
        except urllib.error.URLError as error:
            raise ErrorServicio(
                f"No se pudo consultar la API de cotizaciones: {error}"
            ) from error
        except ValueError as error:
            raise ErrorServicio(
                f"La API devolvió una respuesta inválida: {error}"
            ) from error

    def _siguiente_id_cotizacion(self) -> int:
        """Calcula el próximo id de cotización a partir de los existentes."""
        return _siguiente_id([
            c.id_cotizacion for c in self._repositorio_cotizacion.leer_todos()
        ])


# ---------------------------------------------------------------------------
# ServicioStock
# ---------------------------------------------------------------------------

class ServicioStock:
    """Lógica de negocio para Stock: ingresos, egresos y alertas."""

    def __init__(self, repositorio_stock: RepositorioStock,
                 repositorio_libro: RepositorioLibro) -> None:
        """Crea el servicio.

        Args:
            repositorio_stock (RepositorioStock): Repositorio de stock.
            repositorio_libro (RepositorioLibro): Repositorio de libros.
        """
        self._repositorio_stock = repositorio_stock
        self._repositorio_libro = repositorio_libro

    def crear(self, id_stock: int, libro_id: int,
              cantidad: int = 0,
              cantidad_minima: int = 0) -> Stock:
        """Crea el registro de stock de un libro.

        Args:
            id_stock (int): Identificador del stock.
            libro_id (int): Identificador del libro.
            cantidad (int): Unidades iniciales.
            cantidad_minima (int): Umbral de reposición.

        Returns:
            Stock: El stock creado.

        Raises:
            EntidadNoEncontradaError: Si el libro no existe.
            OperacionInvalidaError: Si el libro ya tiene stock.
        """
        libro = self._repositorio_libro.leer_por_id(libro_id)
        if libro is None:
            raise EntidadNoEncontradaError(
                f"No existe el libro con id {libro_id}"
            )
        if self._repositorio_stock.leer_por_libro(libro_id) is not None:
            raise OperacionInvalidaError(
                f"Ya existe stock para el libro {libro_id}"
            )
        return self._repositorio_stock.crear(
            Stock(
                id_stock=id_stock, cantidad=cantidad,
                cantidad_minima=cantidad_minima, libro=libro,
            )
        )

    def obtener(self, libro_id: int) -> Stock:
        """Devuelve el stock del libro dado.

        Raises:
            EntidadNoEncontradaError: Si el libro no tiene stock.
        """
        stock = self._repositorio_stock.leer_por_libro(libro_id)
        if stock is None:
            raise EntidadNoEncontradaError(
                f"No hay stock registrado para el libro {libro_id}"
            )
        return stock

    def listar(self) -> List[Stock]:
        """Devuelve todos los registros de stock."""
        return self._repositorio_stock.leer_todos()

    def registrar_ingreso(self, libro_id: int, cantidad: int) -> Stock:
        """Suma unidades al stock de un libro.

        Raises:
            OperacionInvalidaError: Si la cantidad no es positiva.
        """
        if cantidad <= 0:
            raise OperacionInvalidaError(
                "La cantidad a ingresar debe ser positiva"
            )
        stock = self.obtener(libro_id)
        stock.cantidad += cantidad
        return self._repositorio_stock.actualizar(stock)

    def registrar_egreso(self, libro_id: int, cantidad: int) -> Stock:
        """Resta unidades al stock de un libro.

        Raises:
            OperacionInvalidaError: Si la cantidad no es positiva o supera
                a la disponible.
        """
        if cantidad <= 0:
            raise OperacionInvalidaError(
                "La cantidad a retirar debe ser positiva"
            )
        stock = self.obtener(libro_id)
        if cantidad > stock.cantidad:
            raise OperacionInvalidaError(
                f"No hay stock suficiente para el libro {libro_id} "
                f"(disponible: {stock.cantidad}, "
                f"solicitado: {cantidad})"
            )
        stock.cantidad -= cantidad
        return self._repositorio_stock.actualizar(stock)

    def eliminar(self, libro_id: int) -> bool:
        """Elimina el registro de stock de un libro. True si existía."""
        return self._repositorio_stock.eliminar(libro_id)

    def hay_alerta_stock_bajo(self, libro_id: int) -> bool:
        """Indica si el stock del libro está en o bajo su mínimo."""
        return self.obtener(libro_id).hay_stock_bajo()


# ---------------------------------------------------------------------------
# ServicioLibro
# ---------------------------------------------------------------------------

class PrecioBimonetario(NamedTuple):
    """Precio de un libro en pesos y en otra moneda.

    Attributes:
        libro (Libro): Libro al que corresponde el precio.
        valor_ars (Optional[float]): Precio en pesos, o None si no puede
            calcularse.
        moneda_destino (str): Código de la moneda consultada.
        valor_destino (Optional[float]): Precio en la moneda consultada, o
            None cuando no existe una cotización que permita calcularlo.
    """

    libro: Libro
    valor_ars: Optional[float]
    moneda_destino: str
    valor_destino: Optional[float]


class ServicioLibro:
    """Lógica de negocio para Libro.

    Crea el libro junto con sus precios y su stock, y valida las relaciones
    con Genero, Editorial y Moneda.
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
        """Crea el servicio.

        Args:
            repositorio_libro (RepositorioLibro): Repositorio de libros.
            repositorio_genero (RepositorioGenero): Repositorio de géneros.
            repositorio_editorial (RepositorioEditorial): Repositorio de
                editoriales.
            repositorio_moneda (RepositorioMoneda): Repositorio de monedas.
            repositorio_precio (RepositorioPrecio): Repositorio de precios.
            repositorio_stock (RepositorioStock): Repositorio de stock.
        """
        self._repositorio_libro = repositorio_libro
        self._repositorio_genero = repositorio_genero
        self._repositorio_editorial = repositorio_editorial
        self._repositorio_moneda = repositorio_moneda
        self._repositorio_precio = repositorio_precio
        self._repositorio_stock = repositorio_stock

    def crear(
        self, id_libro: int, isbn: str, titulo: str, autor: str,
        genero_id: int, editorial_id: int,
        precios: List[Tuple[str, float]],
        cantidad: int = 0, cantidad_minima: int = 0,
    ) -> Libro:
        """Crea un libro con sus precios y su stock en una sola operación.

        Args:
            id_libro (int): Identificador del libro.
            isbn (str): ISBN del libro.
            titulo (str): Título del libro.
            autor (str): Autor del libro.
            genero_id (int): Identificador del género.
            editorial_id (int): Identificador de la editorial.
            precios (List[Tuple[str, float]]): Pares (código de moneda,
                importe); debe incluir uno en pesos y ninguna moneda
                repetida.
            cantidad (int): Unidades iniciales de stock.
            cantidad_minima (int): Umbral de reposición.

        Returns:
            Libro: El libro creado, releído desde la base.

        Raises:
            OperacionInvalidaError: Si el id o el ISBN ya existen, si falta
                el precio en pesos o si una moneda se repite.
            EntidadNoEncontradaError: Si no existe el género, la editorial o
                alguna moneda.
        """
        if self._repositorio_libro.leer_por_id(id_libro) is not None:
            raise OperacionInvalidaError(
                f"Ya existe un libro con id {id_libro}"
            )
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

        codigos = [codigo.upper() for codigo, _ in precios]
        if MONEDA_BASE not in codigos:
            raise OperacionInvalidaError(
                f"El libro debe tener al menos un precio en {MONEDA_BASE}"
            )
        if len(set(codigos)) != len(codigos):
            raise OperacionInvalidaError(
                "No puede haber dos precios en la misma moneda"
            )

        monedas = {m.codigo: m for m in self._repositorio_moneda.leer_todos()}
        proximo_precio = _siguiente_id(
            [p.id_precio for p in self._repositorio_precio.leer_todos()]
        )
        proximo_stock = _siguiente_id(
            [s.id_stock for s in self._repositorio_stock.leer_todos()]
        )

        libro = Libro(
            id_libro=id_libro, isbn=isbn, titulo=titulo, autor=autor,
            editorial=editorial, genero=genero,
        )
        for desplazamiento, (codigo, valor) in enumerate(precios):
            moneda = monedas.get(codigo.upper())
            if moneda is None:
                raise EntidadNoEncontradaError(
                    f"No existe la moneda con código {codigo.upper()}"
                )
            libro.agregar_precio(Precio(
                id_precio=proximo_precio + desplazamiento,
                valor=valor, moneda=moneda,
            ))
        libro.stock = Stock(
            id_stock=proximo_stock, cantidad=cantidad,
            cantidad_minima=cantidad_minima,
        )

        self._repositorio_libro.crear(libro)
        return self.obtener(id_libro)

    def obtener(self, id_libro: int) -> Libro:
        """Devuelve el libro con el id dado.

        Raises:
            EntidadNoEncontradaError: Si no existe.
        """
        libro = self._repositorio_libro.leer_por_id(id_libro)
        if libro is None:
            raise EntidadNoEncontradaError(
                f"No existe el libro con id {id_libro}"
            )
        return libro

    def obtener_por_isbn(self, isbn: str) -> Libro:
        """Devuelve el libro con el ISBN dado.

        Raises:
            EntidadNoEncontradaError: Si no existe.
        """
        libro = self._repositorio_libro.leer_por_isbn(isbn)
        if libro is None:
            raise EntidadNoEncontradaError(
                f"No existe el libro con ISBN {isbn}"
            )
        return libro

    def listar(self) -> List[Libro]:
        """Devuelve todos los libros del catálogo."""
        return self._repositorio_libro.leer_todos()

    def actualizar_datos(self, id_libro: int,
                         titulo: Optional[str] = None,
                         autor: Optional[str] = None,
                         isbn: Optional[str] = None) -> Libro:
        """Modifica el título, el autor y/o el ISBN de un libro.

        Args:
            id_libro (int): Identificador del libro.
            titulo (Optional[str]): Nuevo título; None para no cambiarlo.
            autor (Optional[str]): Nuevo autor; None para no cambiarlo.
            isbn (Optional[str]): Nuevo ISBN; None para no cambiarlo.

        Returns:
            Libro: El libro actualizado.

        Raises:
            OperacionInvalidaError: Si el nuevo ISBN ya lo usa otro libro.
        """
        libro = self.obtener(id_libro)
        if isbn is not None and isbn != libro.isbn:
            otro = self._repositorio_libro.leer_por_isbn(isbn)
            if otro is not None and otro.id_libro != id_libro:
                raise OperacionInvalidaError(
                    f"Ya existe un libro con ISBN {isbn}"
                )
            libro.isbn = isbn
        if titulo is not None:
            libro.titulo = titulo
        if autor is not None:
            libro.autor = autor
        return self._repositorio_libro.actualizar(libro)

    def actualizar_precio(self, id_libro: int, codigo_moneda: str,
                          nuevo_valor: float) -> Libro:
        """Actualiza el precio del libro en una moneda.

        Args:
            id_libro (int): Identificador del libro.
            codigo_moneda (str): Moneda del precio a modificar.
            nuevo_valor (float): Nuevo importe.

        Returns:
            Libro: El libro con el precio actualizado.

        Raises:
            EntidadNoEncontradaError: Si el libro no tiene precio en esa
                moneda.
        """
        libro = self.obtener(id_libro)
        precio = libro.precio_en(codigo_moneda)
        if precio is None:
            raise EntidadNoEncontradaError(
                f"El libro {id_libro} no tiene precio en "
                f"{codigo_moneda.upper()}"
            )
        precio.valor = nuevo_valor
        self._repositorio_precio.actualizar(precio)
        return self.obtener(id_libro)

    def eliminar(self, id_libro: int) -> bool:
        """Elimina un libro junto con sus precios y su stock.

        La eliminación en cascada la resuelve el modelo ORM.

        Raises:
            EntidadNoEncontradaError: Si el libro no existe.
        """
        self.obtener(id_libro)
        return self._repositorio_libro.eliminar(id_libro)

    @staticmethod
    def _valor_ars(libro: Libro,
                   tasas_ars: Dict[str, float]) -> Optional[float]:
        """Calcula el precio del libro en pesos.

        Usa el precio ARS cargado; si no tiene, convierte el de otra moneda
        con la tasa disponible.

        Args:
            libro (Libro): Libro a valuar.
            tasas_ars (Dict[str, float]): Pesos por unidad de cada moneda.

        Returns:
            Optional[float]: Precio en pesos, o None si no se puede calcular.
        """
        precio_ars = libro.precio_en(MONEDA_BASE)
        if precio_ars is not None:
            return precio_ars.valor
        for precio in libro.precios:
            tasa = tasas_ars.get(precio.moneda.codigo)
            if tasa:
                return round(precio.valor * tasa, 2)
        return None

    def _valor_en(self, libro: Libro, codigo: str,
                  tasas_ars: Dict[str, float]) -> Optional[float]:
        """Calcula el precio del libro en una moneda.

        Si el libro ya tiene precio cargado en esa moneda lo usa tal cual;
        si no, convierte su precio en pesos con la tasa de la moneda.

        Args:
            libro (Libro): Libro a valuar.
            codigo (str): Código de la moneda deseada.
            tasas_ars (Dict[str, float]): Pesos por unidad de cada moneda.

        Returns:
            Optional[float]: Precio en la moneda, o None si no hay tasa.
        """
        codigo = codigo.upper()
        propio = libro.precio_en(codigo)
        if propio is not None:
            return propio.valor
        valor_ars = self._valor_ars(libro, tasas_ars)
        tasa = tasas_ars.get(codigo)
        if valor_ars is None or not tasa:
            return None
        return round(valor_ars / tasa, 2)

    def listar_precios_bimonetarios(
        self, moneda_destino: str, tasas_ars: Dict[str, float]
    ) -> List[PrecioBimonetario]:
        """Expresa el precio de cada libro en pesos y en otra moneda.

        Args:
            moneda_destino (str): Código de la moneda a la que se convierte.
            tasas_ars (Dict[str, float]): Pesos por unidad de cada moneda
                (ARS vale 1). Una moneda sin tasa se informa como None.

        Returns:
            List[PrecioBimonetario]: Un registro por cada libro del catálogo.
        """
        tasas = {MONEDA_BASE: 1.0, **tasas_ars}
        return [
            PrecioBimonetario(
                libro=libro,
                valor_ars=self._valor_ars(libro, tasas),
                moneda_destino=moneda_destino.upper(),
                valor_destino=self._valor_en(libro, moneda_destino, tasas),
            )
            for libro in self.listar()
        ]

    def listar_precios_multimonetarios(
        self, codigos_moneda: List[str], tasas_ars: Dict[str, float]
    ) -> List[Tuple[Libro, Dict[str, Optional[float]]]]:
        """Expresa el precio de cada libro en todas las monedas indicadas.

        Args:
            codigos_moneda (List[str]): Códigos de moneda a incluir.
            tasas_ars (Dict[str, float]): Pesos por unidad de cada moneda.

        Returns:
            List[Tuple[Libro, Dict[str, Optional[float]]]]: Un registro por
            libro con el valor en cada moneda. El valor es None cuando no
            hay una cotización que permita calcularlo.
        """
        tasas = {MONEDA_BASE: 1.0, **tasas_ars}
        return [
            (
                libro,
                {
                    codigo.upper(): self._valor_en(libro, codigo, tasas)
                    for codigo in codigos_moneda
                },
            )
            for libro in self.listar()
        ]


# ---------------------------------------------------------------------------
# ServicioScraping
# ---------------------------------------------------------------------------

class ComparacionPrecio(NamedTuple):
    """Comparación del precio interno de un libro con el de la web.

    Attributes:
        libro (Libro): Libro del catálogo.
        precio_interno (float): Precio propio en pesos.
        precio_web (float): Precio en pesos informado por Cúspide.
        diferencia (float): `precio_web - precio_interno`.
        diferencia_pct (float): Diferencia como porcentaje del precio propio.
        url (str): URL de la ficha en Cúspide.
        fecha_extraccion (datetime.datetime): Momento de la extracción.
    """

    libro: Libro
    precio_interno: float
    precio_web: float
    diferencia: float
    diferencia_pct: float
    url: str
    fecha_extraccion: datetime.datetime


class ResultadoScraping(NamedTuple):
    """Resumen de una ejecución del scraper.

    Attributes:
        libros_buscados (int): Libros del catálogo que se buscaron.
        resultados (int): Resultados de Cúspide guardados en la ejecución.
        coincidencias (int): Resultados que coinciden con un libro propio.
        alertas (int): Libros cuya diferencia de precio supera el umbral.
        ruta_alertas (str): Ruta del CSV de alertas generado.
    """

    libros_buscados: int
    resultados: int
    coincidencias: int
    alertas: int
    ruta_alertas: str


# Columnas del archivo CSV de alertas, en orden.
COLUMNAS_ALERTAS = (
    "libro_id", "isbn", "titulo", "precio_interno", "precio_web",
    "diferencia", "diferencia_pct", "tipo_alerta", "url",
    "fecha_extraccion",
)


class _ComparadorPrecios:
    """Base de los servicios que comparan el precio interno con el web."""

    def __init__(self, repositorio_precio_web: RepositorioPrecioWeb,
                 servicio_cotizacion: ServicioCotizacionDolar) -> None:
        """Crea el comparador.

        Args:
            repositorio_precio_web (RepositorioPrecioWeb): Repositorio de los
                precios obtenidos de la web.
            servicio_cotizacion (ServicioCotizacionDolar): Servicio usado
                para convertir dólares a pesos si hiciera falta.
        """
        self._repositorio_precio_web = repositorio_precio_web
        self._servicio_cotizacion = servicio_cotizacion

    def _precio_interno(self, libro: Libro) -> Optional[float]:
        """Devuelve el precio propio del libro en pesos.

        Si el libro no tiene precio en pesos se convierte el de dólares con
        el valor de venta de la cotización Oficial vigente.

        Args:
            libro (Libro): Libro a valuar.

        Returns:
            Optional[float]: El precio en pesos, o None si no hay forma de
            calcularlo.
        """
        precio_ars = libro.precio_en(MONEDA_BASE)
        if precio_ars is not None:
            return precio_ars.valor

        precio_usd = libro.precio_en("USD")
        if precio_usd is None:
            return None
        try:
            oficial = self._servicio_cotizacion.obtener_vigente_por_nombre(
                TIPO_COTIZACION_OFICIAL
            )
        except EntidadNoEncontradaError:
            return None
        return round(precio_usd.valor * oficial.valor_venta, 2)

    def _mejores_coincidencias(self) -> List[PrecioWeb]:
        """Elige la mejor coincidencia de la última extracción de cada libro.

        La mejor es la de mayor similitud de título; ante un empate gana la
        que apareció primero en la búsqueda.

        Returns:
            List[PrecioWeb]: Un precio web por libro, ordenado por libro.
        """
        mejores: Dict[int, PrecioWeb] = {}
        for precio in self._repositorio_precio_web.leer_ultima_extraccion():
            actual = mejores.get(precio.libro.id)
            if actual is None or (
                (precio.similitud or 0.0, -precio.posicion)
                > (actual.similitud or 0.0, -actual.posicion)
            ):
                mejores[precio.libro.id] = precio
        return [mejores[clave] for clave in sorted(mejores)]

    def _comparar_precios(self) -> List[ComparacionPrecio]:
        """Compara el precio interno con el web de cada libro coincidente.

        Se omiten los libros sin precio interno calculable o con precio
        interno cero, porque la diferencia porcentual no estaría definida.

        Returns:
            List[ComparacionPrecio]: Una comparación por libro.
        """
        comparaciones = []
        for web in self._mejores_coincidencias():
            interno = self._precio_interno(web.libro)
            if not interno:
                continue
            diferencia = round(web.precio_web - interno, 2)
            comparaciones.append(ComparacionPrecio(
                libro=web.libro,
                precio_interno=interno,
                precio_web=web.precio_web,
                diferencia=diferencia,
                diferencia_pct=round(diferencia / interno * 100, 2),
                url=web.url,
                fecha_extraccion=web.fecha_extraccion,
            ))
        return comparaciones


class ServicioScraping(_ComparadorPrecios):
    """Ejecuta el scraper de Cúspide para los libros del catálogo.

    Scrapy se ejecuta en un subproceso: el reactor de Twisted no puede
    reiniciarse dentro del mismo proceso y la consola puede pedir el
    scraping varias veces. El pipeline del spider guarda los resultados en la
    base de datos usando `DATABASE_URL`, que el subproceso hereda.
    """

    def __init__(self, repositorio_libro: RepositorioLibro,
                 repositorio_precio_web: RepositorioPrecioWeb,
                 servicio_cotizacion: ServicioCotizacionDolar) -> None:
        """Crea el servicio.

        Args:
            repositorio_libro (RepositorioLibro): Repositorio de libros.
            repositorio_precio_web (RepositorioPrecioWeb): Repositorio de los
                precios obtenidos de la web.
            servicio_cotizacion (ServicioCotizacionDolar): Servicio de
                cotizaciones, para valuar en pesos los libros sin precio ARS.
        """
        super().__init__(repositorio_precio_web, servicio_cotizacion)
        self._repositorio_libro = repositorio_libro

    def ejecutar(self, umbral_pct: float) -> ResultadoScraping:
        """Busca en Cúspide cada libro del catálogo y genera las alertas.

        Args:
            umbral_pct (float): Diferencia mínima de precio, en porcentaje,
                para que un libro genere una alerta.

        Returns:
            ResultadoScraping: Resumen de la ejecución, con la ruta del CSV
            de alertas (que se genera siempre, aunque no haya alertas).

        Raises:
            OperacionInvalidaError: Si el umbral no es positivo o el
                catálogo no tiene libros.
            ErrorServicio: Si el scraper termina con error.
        """
        self._validar_umbral(umbral_pct)
        libros = self._repositorio_libro.leer_todos()
        if not libros:
            raise OperacionInvalidaError(
                "No hay libros en el catálogo para buscar"
            )

        inicio = datetime.datetime.now()
        self._ejecutar_spider(libros)
        extraidos = self._repositorio_precio_web.leer_desde(inicio)

        alertas = self._calcular_alertas(umbral_pct)
        ruta = self._escribir_alertas(alertas, datetime.datetime.now())

        return ResultadoScraping(
            libros_buscados=len(libros),
            resultados=len(extraidos),
            coincidencias=sum(1 for p in extraidos if p.coincide),
            alertas=len(alertas),
            ruta_alertas=ruta,
        )

    def generar_alertas(self, umbral_pct: float,
                        fecha: datetime.datetime) -> str:
        """Genera el CSV de alertas con los últimos precios extraídos.

        Args:
            umbral_pct (float): Diferencia mínima de precio, en porcentaje.
            fecha (datetime.datetime): Momento que da nombre al archivo.

        Returns:
            str: Ruta del archivo `reportes/alertas_YYYYMMDD_HHMMSS.csv`.

        Raises:
            OperacionInvalidaError: Si el umbral no es positivo.
        """
        self._validar_umbral(umbral_pct)
        return self._escribir_alertas(
            self._calcular_alertas(umbral_pct), fecha
        )

    @staticmethod
    def _validar_umbral(umbral_pct: float) -> None:
        """Valida que el umbral sea un porcentaje positivo.

        Raises:
            OperacionInvalidaError: Si el umbral no es mayor que cero.
        """
        if umbral_pct <= 0:
            raise OperacionInvalidaError(
                "El umbral de diferencia debe ser mayor que cero"
            )

    def _calcular_alertas(
        self, umbral_pct: float
    ) -> List[ComparacionPrecio]:
        """Filtra las comparaciones cuya diferencia alcanza el umbral.

        Args:
            umbral_pct (float): Diferencia mínima de precio, en porcentaje.

        Returns:
            List[ComparacionPrecio]: Comparaciones que generan alerta.
        """
        return [
            comparacion for comparacion in self._comparar_precios()
            if abs(comparacion.diferencia_pct) >= umbral_pct
        ]

    @staticmethod
    def _escribir_alertas(alertas: List[ComparacionPrecio],
                          fecha: datetime.datetime) -> str:
        """Escribe el CSV de alertas en la carpeta de reportes.

        Args:
            alertas (List[ComparacionPrecio]): Alertas a escribir; puede
                estar vacía y entonces solo se escribe el encabezado.
            fecha (datetime.datetime): Momento que da nombre al archivo.

        Returns:
            str: Ruta absoluta del archivo generado.
        """
        os.makedirs(CARPETA_REPORTES, exist_ok=True)
        ruta = os.path.abspath(os.path.join(
            CARPETA_REPORTES, f"alertas_{fecha:%Y%m%d_%H%M%S}.csv"
        ))

        with open(ruta, mode="w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_ALERTAS)
            escritor.writeheader()
            for alerta in alertas:
                escritor.writerow({
                    "libro_id": alerta.libro.id_libro,
                    "isbn": alerta.libro.isbn,
                    "titulo": alerta.libro.titulo,
                    "precio_interno": f"{alerta.precio_interno:.2f}",
                    "precio_web": f"{alerta.precio_web:.2f}",
                    "diferencia": f"{alerta.diferencia:.2f}",
                    "diferencia_pct": f"{alerta.diferencia_pct:.2f}",
                    "tipo_alerta": (
                        "MAS_CARO_WEB" if alerta.diferencia > 0
                        else "MAS_BARATO_WEB"
                    ),
                    "url": alerta.url,
                    "fecha_extraccion": (
                        f"{alerta.fecha_extraccion:%Y-%m-%d %H:%M:%S}"
                    ),
                })

        return ruta

    @staticmethod
    def _ejecutar_spider(libros: List[Libro]) -> None:
        """Lanza `scrapy crawl cuspide` en un subproceso.

        Args:
            libros (List[Libro]): Libros del catálogo a buscar.

        Raises:
            ErrorServicio: Si el subproceso termina con error.
        """
        datos = [
            {"id": libro.id_libro, "titulo": libro.titulo, "isbn": libro.isbn}
            for libro in libros
        ]
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "libros.json")
            with open(ruta, mode="w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False)

            entorno = {
                **os.environ,
                "PYTHONPATH": os.pathsep.join(
                    [_CARPETA_SRC, CARPETA_SCRAPER,
                     os.environ.get("PYTHONPATH", "")]
                ),
            }
            proceso = subprocess.run(
                [sys.executable, "-m", "scrapy", "crawl", "cuspide",
                 "-a", f"libros={ruta}"],
                cwd=CARPETA_SCRAPER,
                env=entorno,
                capture_output=True,
                text=True,
            )

        if proceso.returncode != 0:
            detalle = "\n".join(proceso.stderr.strip().splitlines()[-8:])
            raise ErrorServicio(
                f"El scraper terminó con error ({proceso.returncode}):\n"
                f"{detalle}"
            )


# ---------------------------------------------------------------------------
# ServicioReportes
# ---------------------------------------------------------------------------

# Columnas del reporte Excel, en orden.
COLUMNAS_REPORTE = (
    "Libro", "Precio interno", "Precio web", "Diferencia",
    "Fecha de extracción",
)


class ServicioReportes(_ComparadorPrecios):
    """Genera los reportes en Excel a partir de los precios extraídos."""

    def generar_reporte_excel(self) -> str:
        """Genera el reporte Excel que compara el precio interno con el web.

        Tiene una fila por cada libro con coincidencia en la última
        extracción. Si todavía no hay extracciones, el archivo se genera
        solo con los encabezados.

        Returns:
            str: Ruta absoluta del archivo
            `reportes/reporte_precios_YYYYMMDD_HHMMSS.xlsx`.
        """
        filas = [
            {
                "Libro": comparacion.libro.titulo,
                "Precio interno": comparacion.precio_interno,
                "Precio web": comparacion.precio_web,
                "Diferencia": comparacion.diferencia,
                "Fecha de extracción": (
                    f"{comparacion.fecha_extraccion:%Y-%m-%d %H:%M}"
                ),
            }
            for comparacion in self._comparar_precios()
        ]
        tabla = pd.DataFrame(filas, columns=list(COLUMNAS_REPORTE))

        os.makedirs(CARPETA_REPORTES, exist_ok=True)
        ruta = os.path.abspath(os.path.join(
            CARPETA_REPORTES,
            f"reporte_precios_{datetime.datetime.now():%Y%m%d_%H%M%S}.xlsx",
        ))

        with pd.ExcelWriter(ruta, engine="openpyxl") as escritor:
            tabla.to_excel(escritor, index=False, sheet_name="Precios")
            self._ajustar_anchos(escritor.sheets["Precios"], tabla)

        return ruta

    @staticmethod
    def _ajustar_anchos(hoja: Any, tabla: pd.DataFrame) -> None:
        """Ajusta el ancho de cada columna al de su contenido más largo.

        Args:
            hoja (Any): Hoja de openpyxl a ajustar.
            tabla (pd.DataFrame): Datos escritos en la hoja.
        """
        for indice, columna in enumerate(tabla.columns, start=1):
            largo = max(
                [len(str(columna))] + [len(str(v)) for v in tabla[columna]]
            )
            hoja.column_dimensions[get_column_letter(indice)].width = (
                largo + 2
            )
