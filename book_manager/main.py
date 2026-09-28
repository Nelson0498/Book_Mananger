"""
Punto de entrada del sistema Book Manager – Sprint 1.

Ensambla repositorios, servicios, carga datos iniciales y
lanza la interfaz de consola.
"""

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
from book_manager.preload_data.preload_data import cargar_datos_iniciales
from book_manager.ui.console import Consola


def main(import_default_data: bool = True) -> None:
    """Ensambla el sistema y ejecuta la consola."""

    # ------------------------------------------------------------------
    # 1. Repositorios
    # ------------------------------------------------------------------
    repo_genero = RepositorioGenero()
    repo_editorial = RepositorioEditorial()
    repo_moneda = RepositorioMoneda()
    repo_tipo_cotizacion = RepositorioTipoCotizacion()
    repo_precio = RepositorioPrecio(repositorio_moneda=repo_moneda)
    repo_stock = RepositorioStock()
    repo_libro = RepositorioLibro(
        repositorio_genero=repo_genero,
        repositorio_editorial=repo_editorial,
        repositorio_precio=repo_precio,
        repositorio_stock=repo_stock,
    )
    repo_cotizacion = RepositorioCotizacionDolar(
        repositorio_tipo_cotizacion=repo_tipo_cotizacion,
    )

    # ------------------------------------------------------------------
    # 2. Carga de datos iniciales
    # ------------------------------------------------------------------
    cargar_datos_iniciales(
        repo_genero, repo_editorial, repo_moneda, repo_tipo_cotizacion,
        repo_precio, repo_stock, repo_libro, repo_cotizacion,
    )

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
