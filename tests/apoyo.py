"""Utilidades compartidas por las pruebas automatizadas.

Todas las pruebas trabajan contra bases SQLite en memoria: nunca se conectan a
PostgreSQL ni a la instancia remota de Supabase, por lo que no necesitan
credenciales ni conectividad.
"""

from typing import NamedTuple
import os
import shutil
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import event
from sqlalchemy.engine import Engine

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import crear_tablas, migrar_base_de_datos
from book_manager.repositories import repositories as repos
from book_manager.services.services import (
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioStock,
    ServicioTipoCotizacion,
)
from book_manager.ui.console import Consola


# Raíz del proyecto: tests/ -> raíz.
RAIZ_PROYECTO = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)

# Carpeta de trabajo para las pruebas que necesitan escribir archivos. Está
# excluida de Git y se limpia al finalizar cada prueba.
CARPETA_TEMPORAL = os.path.join(RAIZ_PROYECTO, "tests", ".temporal")


@contextmanager
def carpeta_temporal(nombre: str) -> Iterator[str]:
    """Crea una carpeta temporal de pruebas y la elimina al salir.

    Args:
        nombre (str): Nombre de la subcarpeta a utilizar.

    Yields:
        str: Ruta absoluta de la carpeta creada.
    """
    ruta = os.path.join(CARPETA_TEMPORAL, nombre)
    shutil.rmtree(ruta, ignore_errors=True)
    os.makedirs(ruta, exist_ok=True)
    try:
        yield ruta
    finally:
        shutil.rmtree(ruta, ignore_errors=True)


class Repositorios(NamedTuple):
    """Juego completo de repositorios SQLAlchemy sobre una misma conexión."""

    genero: repos.RepositorioGeneroSQLAlchemy
    editorial: repos.RepositorioEditorialSQLAlchemy
    moneda: repos.RepositorioMonedaSQLAlchemy
    tipo_cotizacion: repos.RepositorioTipoCotizacionSQLAlchemy
    precio: repos.RepositorioPrecioSQLAlchemy
    libro: repos.RepositorioLibroSQLAlchemy
    stock: repos.RepositorioStockSQLAlchemy
    cotizacion: repos.RepositorioCotizacionDolarSQLAlchemy


def activar_claves_foraneas(motor: Engine) -> None:
    """Activa la verificación de claves foráneas en SQLite.

    SQLite no las controla por omisión; sin esto las pruebas no detectarían
    problemas de integridad referencial ni de orden de inserción.

    Args:
        motor (Engine): Motor de SQLite sobre el que registrar el evento.
    """

    @event.listens_for(motor, "connect")
    def _al_conectar(conexion_dbapi, _registro):
        conexion_dbapi.execute("PRAGMA foreign_keys=ON")


def crear_conexion_vacia() -> ConexionDB:
    """Devuelve una conexión SQLite en memoria con el esquema y sin datos."""
    conexion = ConexionDB(database_url="sqlite:///:memory:")
    activar_claves_foraneas(conexion.engine)
    crear_tablas(conexion)
    return conexion


def crear_conexion_migrada() -> ConexionDB:
    """Devuelve una conexión SQLite en memoria con el esquema y los datos del TP1."""
    conexion = ConexionDB(database_url="sqlite:///:memory:")
    activar_claves_foraneas(conexion.engine)
    migrar_base_de_datos(conexion)
    return conexion


def crear_repositorios(conexion: ConexionDB) -> Repositorios:
    """Instancia el juego completo de repositorios sobre una conexión.

    Args:
        conexion (ConexionDB): Conexión que utilizarán los repositorios.

    Returns:
        Repositorios: Los ocho repositorios del sistema.
    """
    return Repositorios(
        genero=repos.RepositorioGeneroSQLAlchemy(conexion),
        editorial=repos.RepositorioEditorialSQLAlchemy(conexion),
        moneda=repos.RepositorioMonedaSQLAlchemy(conexion),
        tipo_cotizacion=repos.RepositorioTipoCotizacionSQLAlchemy(conexion),
        precio=repos.RepositorioPrecioSQLAlchemy(conexion),
        libro=repos.RepositorioLibroSQLAlchemy(conexion),
        stock=repos.RepositorioStockSQLAlchemy(conexion),
        cotizacion=repos.RepositorioCotizacionDolarSQLAlchemy(conexion),
    )


class Servicios(NamedTuple):
    """Juego completo de servicios del sistema, ya cableados."""

    genero: ServicioGenero
    editorial: ServicioEditorial
    moneda: ServicioMoneda
    tipo_cotizacion: ServicioTipoCotizacion
    precio: ServicioPrecio
    stock: ServicioStock
    libro: ServicioLibro
    cotizacion: ServicioCotizacionDolar


def crear_servicios(conexion: ConexionDB) -> Servicios:
    """Instancia y cablea todos los servicios sobre una conexión.

    Reproduce el ensamblado que hace `main.py`, para que las pruebas ejerciten
    el mismo grafo de dependencias que la aplicación real.

    Args:
        conexion (ConexionDB): Conexión a utilizar por los repositorios.

    Returns:
        Servicios: Los ocho servicios del sistema.
    """
    repo = crear_repositorios(conexion)

    return Servicios(
        genero=ServicioGenero(repo.genero, repo.libro),
        editorial=ServicioEditorial(repo.editorial, repo.libro),
        moneda=ServicioMoneda(repo.moneda, repo.precio),
        tipo_cotizacion=ServicioTipoCotizacion(
            repo.tipo_cotizacion, repo.cotizacion
        ),
        precio=ServicioPrecio(repo.precio, repo.moneda),
        stock=ServicioStock(repo.stock),
        libro=ServicioLibro(
            repo.libro, repo.genero, repo.editorial,
            repo.moneda, repo.precio, repo.stock,
        ),
        cotizacion=ServicioCotizacionDolar(repo.cotizacion, repo.tipo_cotizacion),
    )


def crear_consola(conexion: ConexionDB) -> Consola:
    """Instancia la consola con los servicios cableados sobre una conexión.

    Args:
        conexion (ConexionDB): Conexión a utilizar.

    Returns:
        Consola: La interfaz de consola lista para invocar sus acciones.
    """
    servicios = crear_servicios(conexion)

    return Consola(
        svc_genero=servicios.genero,
        svc_editorial=servicios.editorial,
        svc_moneda=servicios.moneda,
        svc_tipo_cotizacion=servicios.tipo_cotizacion,
        svc_precio=servicios.precio,
        svc_stock=servicios.stock,
        svc_libro=servicios.libro,
        svc_cotizacion=servicios.cotizacion,
    )
