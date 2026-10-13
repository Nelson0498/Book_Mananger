"""
Punto de entrada del sistema Book Manager – Sprint 2.

Ensambla la conexión a la base de datos, la migración de los datos iniciales,
los repositorios SQLAlchemy, los servicios y lanza la interfaz de consola.
"""

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import (
    crear_tablas,
    migrar_base_de_datos,
)
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolarSQLAlchemy,
    RepositorioEditorialSQLAlchemy,
    RepositorioGeneroSQLAlchemy,
    RepositorioLibroSQLAlchemy,
    RepositorioMonedaSQLAlchemy,
    RepositorioPrecioSQLAlchemy,
    RepositorioStockSQLAlchemy,
    RepositorioTipoCotizacionSQLAlchemy,
)
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


def main(import_default_data: bool = True) -> None:
    """Ensambla el sistema y ejecuta la consola.

    Args:
        import_default_data (bool): Si es True, asegura el esquema y ejecuta la
            migración de los datos del Sprint 1 (archivos CSV) a la base de
            datos. Si es False, no se importa ningún registro: únicamente se
            asegura de que las tablas existan, para que el sistema opere sobre
            los datos ya cargados en la base.
    """
    conexion = ConexionDB()

    try:
        _ejecutar_sistema(conexion, import_default_data)
    finally:
        # Se libera el motor aunque falle la migración, la construcción de los
        # servicios o la ejecución de la consola.
        conexion.cerrar()


def _ejecutar_sistema(conexion: ConexionDB, import_default_data: bool) -> None:
    """Asegura el esquema, arma los servicios y ejecuta la consola.

    Args:
        conexion (ConexionDB): Conexión a la base de datos, ya creada.
        import_default_data (bool): Si es True, ejecuta la migración de datos.
    """

    # ------------------------------------------------------------------
    # 1. Esquema y datos iniciales
    # ------------------------------------------------------------------
    if import_default_data:
        migrar_base_de_datos(conexion)
    else:
        crear_tablas(conexion)

    # ------------------------------------------------------------------
    # 2. Repositorios
    # ------------------------------------------------------------------
    repo_genero = RepositorioGeneroSQLAlchemy(conexion)
    repo_editorial = RepositorioEditorialSQLAlchemy(conexion)
    repo_moneda = RepositorioMonedaSQLAlchemy(conexion)
    repo_tipo_cotizacion = RepositorioTipoCotizacionSQLAlchemy(conexion)
    repo_precio = RepositorioPrecioSQLAlchemy(conexion)
    repo_stock = RepositorioStockSQLAlchemy(conexion)
    repo_libro = RepositorioLibroSQLAlchemy(conexion)
    repo_cotizacion = RepositorioCotizacionDolarSQLAlchemy(conexion)

    # ------------------------------------------------------------------
    # 3. Servicios
    # ------------------------------------------------------------------
    svc_genero = ServicioGenero(repo_genero, repo_libro)
    svc_editorial = ServicioEditorial(repo_editorial, repo_libro)
    svc_moneda = ServicioMoneda(repo_moneda, repo_precio)
    svc_tipo_cotizacion = ServicioTipoCotizacion(
        repo_tipo_cotizacion, repo_cotizacion,
    )
    svc_precio = ServicioPrecio(repo_precio, repo_moneda)
    svc_stock = ServicioStock(repo_stock)
    svc_libro = ServicioLibro(
        repo_libro, repo_genero, repo_editorial,
        repo_moneda, repo_precio, repo_stock,
    )
    svc_cotizacion = ServicioCotizacionDolar(
        repo_cotizacion, repo_tipo_cotizacion,
    )

    # ------------------------------------------------------------------
    # 4. Consola
    # ------------------------------------------------------------------
    consola = Consola(
        svc_genero=svc_genero,
        svc_editorial=svc_editorial,
        svc_moneda=svc_moneda,
        svc_tipo_cotizacion=svc_tipo_cotizacion,
        svc_precio=svc_precio,
        svc_stock=svc_stock,
        svc_libro=svc_libro,
        svc_cotizacion=svc_cotizacion,
    )

    consola.ejecutar()


if __name__ == "__main__":
    main()
