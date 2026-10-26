"""Punto de entrada del sistema Book Manager – Sprint 3.

Ensambla la conexión a la base de datos, la migración de los datos iniciales,
los repositorios, los servicios y lanza la interfaz de consola.
"""

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import (
    CARPETA_CSV_POR_DEFECTO,
    CARPETA_SQL_POR_DEFECTO,
    crear_tablas,
    migrar_datos,
)
from book_manager.preload_data.preload_data import cargar_datos_iniciales
from book_manager.repositories.repositories import (
    RepositorioAuditoria,
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
from book_manager.services.services import (
    ServicioAuditoria,
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioReportes,
    ServicioScraping,
    ServicioStock,
    ServicioTipoCotizacion,
)
from book_manager.ui.console import Consola


def main(import_default_data: bool = True) -> None:
    """Ensambla el sistema y ejecuta la consola.

    Args:
        import_default_data (bool): Si es True, asegura el esquema, genera
            los scripts SQL desde los CSV y los carga en la base de datos. Si
            es False, no se importa ningún registro: únicamente se asegura de
            que las tablas existan, para que el sistema opere sobre los datos
            ya cargados en la base.
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
        import_default_data (bool): Si es True, carga los datos iniciales.
    """

    # ------------------------------------------------------------------
    # 1. Esquema y datos iniciales
    # ------------------------------------------------------------------
    crear_tablas(conexion)
    if import_default_data:
        migrar_datos(CARPETA_CSV_POR_DEFECTO, CARPETA_SQL_POR_DEFECTO)
        cargar_datos_iniciales(conexion, CARPETA_SQL_POR_DEFECTO)

    # ------------------------------------------------------------------
    # 2. Repositorios
    # ------------------------------------------------------------------
    repo_genero = RepositorioGenero(conexion)
    repo_editorial = RepositorioEditorial(conexion)
    repo_moneda = RepositorioMoneda(conexion)
    repo_tipo_cotizacion = RepositorioTipoCotizacion(conexion)
    repo_precio = RepositorioPrecio(conexion)
    repo_stock = RepositorioStock(conexion)
    repo_libro = RepositorioLibro(conexion)
    repo_cotizacion = RepositorioCotizacionDolar(conexion)
    repo_precio_web = RepositorioPrecioWeb(conexion)
    repo_auditoria = RepositorioAuditoria(conexion)

    # ------------------------------------------------------------------
    # 3. Servicios (todos reciben el servicio de auditoría)
    # ------------------------------------------------------------------
    svc_auditoria = ServicioAuditoria(repo_auditoria)
    svc_genero = ServicioGenero(repo_genero, repo_libro, svc_auditoria)
    svc_editorial = ServicioEditorial(
        repo_editorial, repo_libro, svc_auditoria,
    )
    svc_moneda = ServicioMoneda(repo_moneda, repo_precio, svc_auditoria)
    svc_tipo_cotizacion = ServicioTipoCotizacion(
        repo_tipo_cotizacion, repo_cotizacion, svc_auditoria,
    )
    svc_precio = ServicioPrecio(
        repo_precio, repo_moneda, repo_libro, svc_auditoria,
    )
    svc_stock = ServicioStock(repo_stock, repo_libro, svc_auditoria)
    svc_libro = ServicioLibro(
        repo_libro, repo_genero, repo_editorial,
        repo_moneda, repo_precio, repo_stock, svc_auditoria,
    )
    svc_cotizacion = ServicioCotizacionDolar(
        repo_cotizacion, repo_tipo_cotizacion, svc_auditoria,
    )
    svc_scraping = ServicioScraping(
        repo_libro, repo_precio_web, svc_cotizacion, svc_auditoria,
    )
    svc_reportes = ServicioReportes(
        repo_precio_web, svc_cotizacion, svc_auditoria,
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
        svc_scraping=svc_scraping,
        svc_reportes=svc_reportes,
    )

    consola.ejecutar()


if __name__ == "__main__":
    main()
