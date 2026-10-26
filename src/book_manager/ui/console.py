"""Interfaz de consola (CLI) para el sistema Book Manager.

Presenta menús interactivos para realizar CRUD sobre todas las
entidades del sistema.  Toda la lógica de negocio se delega a
los servicios; la consola solo se encarga de pedir datos al
usuario, llamar al servicio correspondiente y mostrar resultados.
"""

import csv
import datetime
import os
from typing import Dict, List, Optional

from pydantic import ValidationError

from book_manager.entities.entities import CotizacionDolar
from book_manager.schemas.schemas import (
    CotizacionDolarInput,
    CotizacionDolarUpdateInput,
    EditorialInput,
    EditorialUpdateInput,
    GeneroInput,
    GeneroUpdateInput,
    LibroInput,
    LibroPrecioUpdateInput,
    LibroUpdateInput,
    MonedaInput,
    MonedaUpdateInput,
    PrecioInput,
    PrecioLibroInput,
    PrecioUpdateInput,
    StockInput,
    StockMovimientoInput,
    TipoCotizacionInput,
    TipoCotizacionUpdateInput,
)
from book_manager.services.services import (
    CARPETA_REPORTES,
    EntidadNoEncontradaError,
    ErrorServicio,
    MONEDA_BASE,
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioScraping,
    ServicioStock,
    ServicioTipoCotizacion,
    TIPO_COTIZACION_OFICIAL,
)

# En Google Colab los archivos generados se pueden descargar al equipo.
try:
    from google.colab import files as archivos_colab
except ImportError:
    archivos_colab = None


# ---------------------------------------------------------------------------
# Helpers de entrada
# ---------------------------------------------------------------------------

def pedir_entero(mensaje: str) -> int:
    """Pide al usuario un número entero, reintentando ante errores."""
    while True:
        try:
            return int(input(mensaje))
        except ValueError:
            print("  Error: debe ingresar un número entero.")


def pedir_float(mensaje: str) -> float:
    """Pide al usuario un número decimal, reintentando ante errores."""
    while True:
        try:
            return float(input(mensaje))
        except ValueError:
            print("  Error: debe ingresar un número decimal.")


def pedir_texto(mensaje: str, permitir_vacio: bool = False) -> str:
    """Pide al usuario un texto, reintentando si no se permite vacío."""
    while True:
        valor = input(mensaje).strip()
        if valor or permitir_vacio:
            return valor
        print("  Error: el campo no puede estar vacío.")


def pedir_texto_opcional(mensaje: str) -> Optional[str]:
    """Pide un texto al usuario; devuelve None si está vacío."""
    valor = input(mensaje).strip()
    return valor if valor else None


def pedir_fecha(mensaje: str) -> datetime.date:
    """Pide una fecha en formato AAAA-MM-DD, reintentando ante errores."""
    while True:
        texto = input(mensaje).strip()
        try:
            return datetime.date.fromisoformat(texto)
        except ValueError:
            print("  Error: formato inválido. Use AAAA-MM-DD.")


def pedir_opcion(mensaje: str, opciones_validas: list) -> str:
    """Pide una opción de un conjunto válido, reintentando ante errores."""
    while True:
        opcion = input(mensaje).strip()
        if opcion in opciones_validas:
            return opcion
        print(f"  Opción inválida. Opciones: {', '.join(opciones_validas)}")


def mostrar_titulo(titulo: str) -> None:
    """Imprime un título enmarcado."""
    print(f"\n{'='*50}")
    print(f"  {titulo}")
    print(f"{'='*50}")


def pausar() -> None:
    """Pausa hasta que el usuario presione Enter."""
    input("\n  Presione Enter para continuar...")


# ---------------------------------------------------------------------------
# Clase Consola
# ---------------------------------------------------------------------------

class Consola:
    """Interfaz de consola que opera con los servicios del sistema."""

    def __init__(
        self,
        svc_genero: ServicioGenero,
        svc_editorial: ServicioEditorial,
        svc_moneda: ServicioMoneda,
        svc_tipo_cotizacion: ServicioTipoCotizacion,
        svc_precio: ServicioPrecio,
        svc_stock: ServicioStock,
        svc_libro: ServicioLibro,
        svc_cotizacion: ServicioCotizacionDolar,
        svc_scraping: ServicioScraping,
    ) -> None:
        """Crea la consola con los servicios que utiliza.

        Args:
            svc_genero (ServicioGenero): Servicio de géneros.
            svc_editorial (ServicioEditorial): Servicio de editoriales.
            svc_moneda (ServicioMoneda): Servicio de monedas.
            svc_tipo_cotizacion (ServicioTipoCotizacion): Servicio de tipos
                de cotización.
            svc_precio (ServicioPrecio): Servicio de precios.
            svc_stock (ServicioStock): Servicio de stock.
            svc_libro (ServicioLibro): Servicio de libros.
            svc_cotizacion (ServicioCotizacionDolar): Servicio de
                cotizaciones del dólar.
            svc_scraping (ServicioScraping): Servicio de scraping y alertas.
        """
        self._svc_genero = svc_genero
        self._svc_editorial = svc_editorial
        self._svc_moneda = svc_moneda
        self._svc_tipo_cotizacion = svc_tipo_cotizacion
        self._svc_precio = svc_precio
        self._svc_stock = svc_stock
        self._svc_libro = svc_libro
        self._svc_cotizacion = svc_cotizacion
        self._svc_scraping = svc_scraping

    # ==================================================================
    # Menú principal
    # ==================================================================

    def ejecutar(self) -> None:
        """Bucle principal del menú."""
        while True:
            mostrar_titulo("BOOK MANAGER")
            print("  1. Libros")
            print("  2. Géneros")
            print("  3. Editoriales")
            print("  4. Monedas")
            print("  5. Precios")
            print("  6. Stock")
            print("  7. Tipos de Cotización")
            print("  8. Cotizaciones del Dólar")
            print("  9. Obtener cotizaciones por API")
            print(" 10. Lista de precios bimonetaria")
            print(" 11. Exportar precios a CSV")
            print("  0. Salir")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
            )

            if opcion == "1":
                self._menu_libros()
            elif opcion == "2":
                self._menu_generos()
            elif opcion == "3":
                self._menu_editoriales()
            elif opcion == "4":
                self._menu_monedas()
            elif opcion == "5":
                self._menu_precios()
            elif opcion == "6":
                self._menu_stock()
            elif opcion == "7":
                self._menu_tipos_cotizacion()
            elif opcion == "8":
                self._menu_cotizaciones()
            elif opcion in ("9", "10", "11"):
                try:
                    if opcion == "9":
                        self._obtener_cotizaciones_api()
                    elif opcion == "10":
                        self._lista_precios_bimonetaria()
                    else:
                        self._exportar_precios_csv()
                except (ErrorServicio, ValidationError, ValueError) as e:
                    print(f"\n  Error: {e}")
                pausar()
            elif opcion == "0":
                print("\n  ¡Hasta luego!")
                break

    # ==================================================================
    # Géneros
    # ==================================================================

    def _menu_generos(self) -> None:
        """Muestra el menú de géneros y ejecuta la opción elegida."""
        while True:
            mostrar_titulo("GÉNEROS")
            print("  1. Crear")
            print("  2. Listar")
            print("  3. Buscar por ID")
            print("  4. Modificar")
            print("  5. Eliminar")
            print("  0. Volver")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5"],
            )

            try:
                if opcion == "1":
                    self._crear_genero()
                elif opcion == "2":
                    self._listar_generos()
                elif opcion == "3":
                    self._buscar_genero()
                elif opcion == "4":
                    self._modificar_genero()
                elif opcion == "5":
                    self._eliminar_genero()
                elif opcion == "0":
                    break
            except (ErrorServicio, ValidationError, ValueError) as e:
                print(f"\n  Error: {e}")
            pausar()

    def _crear_genero(self) -> None:
        """Pide los datos y crea un género."""
        print("\n  --- Crear Género ---")
        id_genero = pedir_entero("  ID: ")
        nombre = pedir_texto("  Nombre: ")
        datos = GeneroInput(id_genero=id_genero, nombre=nombre)
        genero = self._svc_genero.crear(datos.id_genero, datos.nombre)
        print(f"\n  Género creado: {genero}")

    def _listar_generos(self) -> None:
        """Lista géneros."""
        print("\n  --- Listado de Géneros ---")
        generos = self._svc_genero.listar()
        if not generos:
            print("  No hay géneros registrados.")
            return
        for g in generos:
            print(f"  ID: {g.id_genero} | Nombre: {g.nombre}")

    def _buscar_genero(self) -> None:
        """Busca un género por su ID y lo muestra."""
        print("\n  --- Buscar Género ---")
        id_genero = pedir_entero("  ID: ")
        genero = self._svc_genero.obtener(id_genero)
        print(f"\n  ID: {genero.id_genero} | Nombre: {genero.nombre}")

    def _modificar_genero(self) -> None:
        """Pide los datos y modifica un género."""
        print("\n  --- Modificar Género ---")
        id_genero = pedir_entero("  ID del género a modificar: ")
        nuevo_nombre = pedir_texto("  Nuevo nombre: ")
        datos = GeneroUpdateInput(
            id_genero=id_genero, nuevo_nombre=nuevo_nombre,
        )
        genero = self._svc_genero.actualizar_nombre(
            datos.id_genero, datos.nuevo_nombre,
        )
        print(f"\n  Género actualizado: {genero}")

    def _eliminar_genero(self) -> None:
        """Pide el ID y elimina un género."""
        print("\n  --- Eliminar Género ---")
        id_genero = pedir_entero("  ID del género a eliminar: ")
        self._svc_genero.eliminar(id_genero)
        print("\n  Género eliminado correctamente.")

    # ==================================================================
    # Editoriales
    # ==================================================================

    def _menu_editoriales(self) -> None:
        """Muestra el menú de editoriales y ejecuta la opción elegida."""
        while True:
            mostrar_titulo("EDITORIALES")
            print("  1. Crear")
            print("  2. Listar")
            print("  3. Buscar por ID")
            print("  4. Modificar")
            print("  5. Eliminar")
            print("  0. Volver")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5"],
            )

            try:
                if opcion == "1":
                    self._crear_editorial()
                elif opcion == "2":
                    self._listar_editoriales()
                elif opcion == "3":
                    self._buscar_editorial()
                elif opcion == "4":
                    self._modificar_editorial()
                elif opcion == "5":
                    self._eliminar_editorial()
                elif opcion == "0":
                    break
            except (ErrorServicio, ValidationError, ValueError) as e:
                print(f"\n  Error: {e}")
            pausar()

    def _crear_editorial(self) -> None:
        """Pide los datos y crea una editorial."""
        print("\n  --- Crear Editorial ---")
        id_editorial = pedir_entero("  ID: ")
        nombre = pedir_texto("  Nombre: ")
        pais = pedir_texto_opcional("  País (Enter para omitir): ")
        datos = EditorialInput(
            id_editorial=id_editorial, nombre=nombre, pais=pais,
        )
        editorial = self._svc_editorial.crear(
            datos.id_editorial, datos.nombre, datos.pais,
        )
        print(f"\n  Editorial creada: {editorial}")

    def _listar_editoriales(self) -> None:
        """Lista editoriales."""
        print("\n  --- Listado de Editoriales ---")
        editoriales = self._svc_editorial.listar()
        if not editoriales:
            print("  No hay editoriales registradas.")
            return
        for e in editoriales:
            pais = e.pais or "N/D"
            print(f"  ID: {e.id_editorial} | {e.nombre} | País: {pais}")

    def _buscar_editorial(self) -> None:
        """Busca una editorial por su ID y lo muestra."""
        print("\n  --- Buscar Editorial ---")
        id_editorial = pedir_entero("  ID: ")
        editorial = self._svc_editorial.obtener(id_editorial)
        pais = editorial.pais or "N/D"
        print(f"\n  ID: {editorial.id_editorial} | {editorial.nombre}"
              f" | País: {pais}")

    def _modificar_editorial(self) -> None:
        """Pide los datos y modifica una editorial."""
        print("\n  --- Modificar Editorial ---")
        id_editorial = pedir_entero("  ID de la editorial a modificar: ")
        print("  (Deje vacío para no modificar)")
        nombre = pedir_texto_opcional("  Nuevo nombre: ")
        pais = pedir_texto_opcional("  Nuevo país: ")
        datos = EditorialUpdateInput(
            id_editorial=id_editorial, nombre=nombre, pais=pais,
        )
        editorial = self._svc_editorial.actualizar(
            datos.id_editorial, nombre=datos.nombre, pais=datos.pais,
        )
        print(f"\n  Editorial actualizada: {editorial}")

    def _eliminar_editorial(self) -> None:
        """Pide el ID y elimina una editorial."""
        print("\n  --- Eliminar Editorial ---")
        id_editorial = pedir_entero("  ID de la editorial a eliminar: ")
        self._svc_editorial.eliminar(id_editorial)
        print("\n  Editorial eliminada correctamente.")

    # ==================================================================
    # Monedas
    # ==================================================================

    def _menu_monedas(self) -> None:
        """Muestra el menú de monedas y ejecuta la opción elegida."""
        while True:
            mostrar_titulo("MONEDAS")
            print("  1. Crear")
            print("  2. Listar")
            print("  3. Buscar por ID")
            print("  4. Modificar")
            print("  5. Eliminar")
            print("  0. Volver")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5"],
            )

            try:
                if opcion == "1":
                    self._crear_moneda()
                elif opcion == "2":
                    self._listar_monedas()
                elif opcion == "3":
                    self._buscar_moneda()
                elif opcion == "4":
                    self._modificar_moneda()
                elif opcion == "5":
                    self._eliminar_moneda()
                elif opcion == "0":
                    break
            except (ErrorServicio, ValidationError, ValueError) as e:
                print(f"\n  Error: {e}")
            pausar()

    def _crear_moneda(self) -> None:
        """Pide los datos y crea una moneda."""
        print("\n  --- Crear Moneda ---")
        id_moneda = pedir_entero("  ID: ")
        codigo = pedir_texto("  Código (ej: USD): ")
        nombre = pedir_texto("  Nombre: ")
        simbolo = pedir_texto("  Símbolo (ej: US$): ")
        datos = MonedaInput(
            id_moneda=id_moneda, codigo=codigo,
            nombre=nombre, simbolo=simbolo,
        )
        moneda = self._svc_moneda.crear(
            datos.id_moneda, datos.codigo,
            datos.nombre, datos.simbolo,
        )
        print(f"\n  Moneda creada: {moneda}")

    def _listar_monedas(self) -> None:
        """Lista monedas."""
        print("\n  --- Listado de Monedas ---")
        monedas = self._svc_moneda.listar()
        if not monedas:
            print("  No hay monedas registradas.")
            return
        for m in monedas:
            print(f"  ID: {m.id_moneda} | {m.codigo} | {m.nombre}"
                  f" | {m.simbolo}")

    def _buscar_moneda(self) -> None:
        """Busca una moneda por su ID y lo muestra."""
        print("\n  --- Buscar Moneda ---")
        id_moneda = pedir_entero("  ID: ")
        moneda = self._svc_moneda.obtener(id_moneda)
        print(f"\n  ID: {moneda.id_moneda} | {moneda.codigo}"
              f" | {moneda.nombre} | {moneda.simbolo}")

    def _modificar_moneda(self) -> None:
        """Pide los datos y modifica una moneda."""
        print("\n  --- Modificar Moneda ---")
        id_moneda = pedir_entero("  ID de la moneda a modificar: ")
        print("  (Deje vacío para no modificar)")
        nombre = pedir_texto_opcional("  Nuevo nombre: ")
        simbolo = pedir_texto_opcional("  Nuevo símbolo: ")
        datos = MonedaUpdateInput(
            id_moneda=id_moneda, nombre=nombre, simbolo=simbolo,
        )
        moneda = self._svc_moneda.actualizar(
            datos.id_moneda, nombre=datos.nombre, simbolo=datos.simbolo,
        )
        print(f"\n  Moneda actualizada: {moneda}")

    def _eliminar_moneda(self) -> None:
        """Pide el ID y elimina una moneda."""
        print("\n  --- Eliminar Moneda ---")
        id_moneda = pedir_entero("  ID de la moneda a eliminar: ")
        self._svc_moneda.eliminar(id_moneda)
        print("\n  Moneda eliminada correctamente.")

    # ==================================================================
    # Precios
    # ==================================================================

    def _menu_precios(self) -> None:
        """Muestra el menú de precios y ejecuta la opción elegida."""
        while True:
            mostrar_titulo("PRECIOS")
            print("  1. Agregar precio a un libro")
            print("  2. Listar todos")
            print("  3. Listar precios de un libro")
            print("  4. Buscar por ID")
            print("  5. Modificar")
            print("  6. Eliminar")
            print("  0. Volver")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5", "6"],
            )

            try:
                if opcion == "1":
                    self._crear_precio()
                elif opcion == "2":
                    self._listar_precios()
                elif opcion == "3":
                    self._listar_precios_de_libro()
                elif opcion == "4":
                    self._buscar_precio()
                elif opcion == "5":
                    self._modificar_precio()
                elif opcion == "6":
                    self._eliminar_precio()
                elif opcion == "0":
                    break
            except (ErrorServicio, ValidationError, ValueError) as e:
                print(f"\n  Error: {e}")
            pausar()

    def _crear_precio(self) -> None:
        """Pide los datos y crea un precio."""
        print("\n  --- Agregar Precio a un Libro ---")
        libro_id = pedir_entero("  ID del libro: ")
        print("  Monedas disponibles:")
        for m in self._svc_moneda.listar():
            print(f"    {m.codigo} – {m.nombre}")
        codigo = pedir_texto("  Código de la moneda: ")
        valor = pedir_float("  Valor: ")
        datos = PrecioInput(
            libro_id=libro_id, codigo_moneda=codigo, valor=valor,
        )
        precio = self._svc_precio.agregar(
            datos.libro_id, datos.codigo_moneda, datos.valor,
        )
        print(f"\n  Precio creado: {precio}")

    def _listar_precios(self) -> None:
        """Lista precios."""
        print("\n  --- Listado de Precios ---")
        precios = self._svc_precio.listar()
        if not precios:
            print("  No hay precios registrados.")
            return
        for p in precios:
            print(f"  ID: {p.id_precio} | Libro: {p.libro.id_libro}"
                  f" | {p.valor:.2f} {p.moneda.codigo}")

    def _listar_precios_de_libro(self) -> None:
        """Lista los precios de un libro."""
        print("\n  --- Precios de un Libro ---")
        libro_id = pedir_entero("  ID del libro: ")
        precios = self._svc_precio.listar_por_libro(libro_id)
        if not precios:
            print("  El libro no tiene precios registrados.")
            return
        for p in precios:
            print(f"  ID: {p.id_precio} | {p.valor:.2f} {p.moneda.codigo}"
                  f" ({p.moneda.nombre})")

    def _buscar_precio(self) -> None:
        """Busca un precio por su ID y lo muestra."""
        print("\n  --- Buscar Precio ---")
        id_precio = pedir_entero("  ID: ")
        precio = self._svc_precio.obtener(id_precio)
        print(f"\n  ID: {precio.id_precio} | Libro: {precio.libro.titulo}"
              f" | {precio.valor:.2f} {precio.moneda.codigo}"
              f" ({precio.moneda.nombre})")

    def _modificar_precio(self) -> None:
        """Pide los datos y modifica un precio."""
        print("\n  --- Modificar Precio ---")
        id_precio = pedir_entero("  ID del precio a modificar: ")
        nuevo_valor = pedir_float("  Nuevo valor: ")
        datos = PrecioUpdateInput(
            id_precio=id_precio, nuevo_valor=nuevo_valor,
        )
        precio = self._svc_precio.actualizar(
            datos.id_precio, nuevo_valor=datos.nuevo_valor,
        )
        print(f"\n  Precio actualizado: {precio}")

    def _eliminar_precio(self) -> None:
        """Pide el ID y elimina un precio."""
        print("\n  --- Eliminar Precio ---")
        id_precio = pedir_entero("  ID del precio a eliminar: ")
        self._svc_precio.eliminar(id_precio)
        print("\n  Precio eliminado correctamente.")

    # ==================================================================
    # Stock
    # ==================================================================

    def _menu_stock(self) -> None:
        """Muestra el menú de stock y ejecuta la opción elegida."""
        while True:
            mostrar_titulo("STOCK")
            print("  1. Crear")
            print("  2. Consultar por ID de libro")
            print("  3. Listar todos")
            print("  4. Registrar ingreso")
            print("  5. Registrar egreso")
            print("  6. Consultar alerta de stock bajo")
            print("  7. Eliminar")
            print("  0. Volver")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5", "6", "7"],
            )

            try:
                if opcion == "1":
                    self._crear_stock()
                elif opcion == "2":
                    self._consultar_stock()
                elif opcion == "3":
                    self._listar_stocks()
                elif opcion == "4":
                    self._registrar_ingreso()
                elif opcion == "5":
                    self._registrar_egreso()
                elif opcion == "6":
                    self._alerta_stock_bajo()
                elif opcion == "7":
                    self._eliminar_stock()
                elif opcion == "0":
                    break
            except (ErrorServicio, ValidationError, ValueError) as e:
                print(f"\n  Error: {e}")
            pausar()

    def _crear_stock(self) -> None:
        """Pide los datos y crea un registro de stock."""
        print("\n  --- Crear Stock ---")
        id_stock = pedir_entero("  ID del stock: ")
        libro_id = pedir_entero("  ID del libro: ")
        cantidad = pedir_entero("  Cantidad inicial: ")
        cantidad_minima = pedir_entero("  Cantidad mínima: ")
        datos = StockInput(
            id_stock=id_stock, libro_id=libro_id,
            cantidad=cantidad, cantidad_minima=cantidad_minima,
        )
        stock = self._svc_stock.crear(
            datos.id_stock, datos.libro_id,
            datos.cantidad, datos.cantidad_minima,
        )
        print(f"\n  Stock creado: {stock}")

    def _consultar_stock(self) -> None:
        """Consulta el stock de un libro."""
        print("\n  --- Consultar Stock ---")
        libro_id = pedir_entero("  ID del libro: ")
        stock = self._svc_stock.obtener(libro_id)
        print(f"\n  Libro: {stock.libro.id_libro} | {stock.libro.titulo}")
        print(f"  Cantidad: {stock.cantidad}")
        print(f"  Cantidad mínima: {stock.cantidad_minima}")
        print(f"  Stock bajo: {'Sí' if stock.hay_stock_bajo() else 'No'}")

    def _listar_stocks(self) -> None:
        """Lista los registros de stock."""
        print("\n  --- Listado de Stock ---")
        stocks = self._svc_stock.listar()
        if not stocks:
            print("  No hay stocks registrados.")
            return
        for s in stocks:
            alerta = " ⚠ BAJO" if s.hay_stock_bajo() else ""
            print(f"  Libro: {s.libro.id_libro} | {s.libro.titulo[:30]}"
                  f" | Cant: {s.cantidad}"
                  f" | Min: {s.cantidad_minima}{alerta}")

    def _registrar_ingreso(self) -> None:
        """Pide los datos y registra un ingreso de stock."""
        print("\n  --- Registrar Ingreso ---")
        libro_id = pedir_entero("  ID del libro: ")
        cantidad = pedir_entero("  Cantidad a ingresar: ")
        datos = StockMovimientoInput(libro_id=libro_id, cantidad=cantidad)
        stock = self._svc_stock.registrar_ingreso(
            datos.libro_id, datos.cantidad,
        )
        print(f"\n  Ingreso registrado. Stock actual: {stock.cantidad}")

    def _registrar_egreso(self) -> None:
        """Pide los datos y registra un egreso de stock."""
        print("\n  --- Registrar Egreso ---")
        libro_id = pedir_entero("  ID del libro: ")
        cantidad = pedir_entero("  Cantidad a retirar: ")
        datos = StockMovimientoInput(libro_id=libro_id, cantidad=cantidad)
        stock = self._svc_stock.registrar_egreso(
            datos.libro_id, datos.cantidad,
        )
        print(f"\n  Egreso registrado. Stock actual: {stock.cantidad}")

    def _alerta_stock_bajo(self) -> None:
        """Consulta si el stock de un libro está bajo el mínimo."""
        print("\n  --- Alerta de Stock Bajo ---")
        libro_id = pedir_entero("  ID del libro: ")
        alerta = self._svc_stock.hay_alerta_stock_bajo(libro_id)
        if alerta:
            print("\n  ⚠ ALERTA: el stock está bajo el mínimo.")
        else:
            print("\n  El stock está dentro de los niveles normales.")

    def _eliminar_stock(self) -> None:
        """Pide el ID y elimina un registro de stock."""
        print("\n  --- Eliminar Stock ---")
        libro_id = pedir_entero("  ID del libro: ")
        eliminado = self._svc_stock.eliminar(libro_id)
        if eliminado:
            print("\n  Stock eliminado correctamente.")
        else:
            print("\n  No se encontró stock para ese libro.")

    # ==================================================================
    # Libros
    # ==================================================================

    def _menu_libros(self) -> None:
        """Muestra el menú de libros y ejecuta la opción elegida."""
        while True:
            mostrar_titulo("LIBROS")
            print("  1. Crear")
            print("  2. Listar")
            print("  3. Buscar por ID")
            print("  4. Modificar datos")
            print("  5. Modificar precio")
            print("  6. Eliminar")
            print("  0. Volver")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5", "6"],
            )

            try:
                if opcion == "1":
                    self._crear_libro()
                elif opcion == "2":
                    self._listar_libros()
                elif opcion == "3":
                    self._buscar_libro()
                elif opcion == "4":
                    self._modificar_libro()
                elif opcion == "5":
                    self._modificar_precio_libro()
                elif opcion == "6":
                    self._eliminar_libro()
                elif opcion == "0":
                    break
            except (ErrorServicio, ValidationError, ValueError) as e:
                print(f"\n  Error: {e}")
            pausar()

    def _pedir_precios_libro(self) -> List[PrecioLibroInput]:
        """Pide el precio en pesos y los de otras monedas de un libro."""
        print("\n  Monedas disponibles:")
        for m in self._svc_moneda.listar():
            print(f"    {m.codigo} – {m.nombre}")

        precios = [PrecioLibroInput(
            codigo_moneda=MONEDA_BASE,
            valor=pedir_float(f"  Precio en {MONEDA_BASE}: "),
        )]
        usadas = {MONEDA_BASE}
        while pedir_opcion(
            "  ¿Agregar precio en otra moneda? (s/n): ", ["s", "n"]
        ) == "s":
            codigo = pedir_texto("  Código de la moneda: ").upper()
            if codigo in usadas:
                print(f"  Error: ya se cargó un precio en {codigo}.")
                continue
            precios.append(PrecioLibroInput(
                codigo_moneda=codigo,
                valor=pedir_float(f"  Precio en {codigo}: "),
            ))
            usadas.add(codigo)
        return precios

    def _crear_libro(self) -> None:
        """Pide los datos y crea un libro."""
        print("\n  --- Crear Libro ---")

        id_libro = pedir_entero("  ID del libro: ")
        isbn = pedir_texto("  ISBN: ")
        titulo = pedir_texto("  Título: ")
        autor = pedir_texto("  Autor: ")

        print("\n  Géneros disponibles:")
        for g in self._svc_genero.listar():
            print(f"    ID: {g.id_genero} | {g.nombre}")
        genero_id = pedir_entero("  ID del género: ")

        print("\n  Editoriales disponibles:")
        for e in self._svc_editorial.listar():
            print(f"    ID: {e.id_editorial} | {e.nombre}")
        editorial_id = pedir_entero("  ID de la editorial: ")

        precios = self._pedir_precios_libro()

        cantidad_inicial = pedir_entero("  Cantidad inicial de stock: ")
        cantidad_minima = pedir_entero("  Cantidad mínima de stock: ")

        datos = LibroInput(
            id_libro=id_libro, isbn=isbn, titulo=titulo, autor=autor,
            editorial_id=editorial_id, genero_id=genero_id,
            precios=precios,
            cantidad_inicial=cantidad_inicial,
            cantidad_minima=cantidad_minima,
        )

        libro = self._svc_libro.crear(
            id_libro=datos.id_libro, isbn=datos.isbn, titulo=datos.titulo,
            autor=datos.autor, genero_id=datos.genero_id,
            editorial_id=datos.editorial_id,
            precios=[(p.codigo_moneda, p.valor) for p in datos.precios],
            cantidad=datos.cantidad_inicial,
            cantidad_minima=datos.cantidad_minima,
        )
        print(f"\n  Libro creado: {libro}")

    def _listar_libros(self) -> None:
        """Lista libros."""
        print("\n  --- Listado de Libros ---")
        libros = self._svc_libro.listar()
        if not libros:
            print("  No hay libros registrados.")
            return
        for libro in libros:
            precios = " / ".join(str(p) for p in libro.precios)
            cantidad = libro.stock.cantidad if libro.stock else 0
            print(f"  ID: {libro.id_libro} | {libro.isbn} | {libro.titulo}"
                  f" | {libro.autor} | {precios} | Stock: {cantidad}")

    def _buscar_libro(self) -> None:
        """Busca un libro por su ID y lo muestra."""
        print("\n  --- Buscar Libro ---")
        id_libro = pedir_entero("  ID: ")
        libro = self._svc_libro.obtener(id_libro)
        print(f"\n  ID:        {libro.id_libro}")
        print(f"  ISBN:      {libro.isbn}")
        print(f"  Título:    {libro.titulo}")
        print(f"  Autor:     {libro.autor}")
        print(f"  Editorial: {libro.editorial.nombre}")
        print(f"  Género:    {libro.genero.nombre}")
        for precio in libro.precios:
            print(f"  Precio:    {precio}")
        if libro.stock is not None:
            print(f"  Stock:     {libro.stock.cantidad} "
                  f"(mín: {libro.stock.cantidad_minima})")

    def _modificar_libro(self) -> None:
        """Pide los datos y modifica un libro."""
        print("\n  --- Modificar Libro ---")
        id_libro = pedir_entero("  ID del libro a modificar: ")
        print("  (Deje vacío para no modificar)")
        isbn = pedir_texto_opcional("  Nuevo ISBN: ")
        titulo = pedir_texto_opcional("  Nuevo título: ")
        autor = pedir_texto_opcional("  Nuevo autor: ")
        datos = LibroUpdateInput(
            id_libro=id_libro, isbn=isbn, titulo=titulo, autor=autor,
        )
        libro = self._svc_libro.actualizar_datos(
            datos.id_libro, titulo=datos.titulo, autor=datos.autor,
            isbn=datos.isbn,
        )
        print(f"\n  Libro actualizado: {libro}")

    def _modificar_precio_libro(self) -> None:
        """Pide los datos y modifica el precio de un libro."""
        print("\n  --- Modificar Precio del Libro ---")
        id_libro = pedir_entero("  ID del libro: ")
        codigo = pedir_texto("  Código de la moneda del precio: ")
        nuevo_valor = pedir_float("  Nuevo valor del precio: ")
        datos = LibroPrecioUpdateInput(
            id_libro=id_libro, codigo_moneda=codigo,
            nuevo_valor=nuevo_valor,
        )
        libro = self._svc_libro.actualizar_precio(
            datos.id_libro, datos.codigo_moneda, datos.nuevo_valor,
        )
        precios = ", ".join(str(p) for p in libro.precios)
        print(f"\n  Precios actualizados: {precios}")

    def _eliminar_libro(self) -> None:
        """Pide el ID y elimina un libro."""
        print("\n  --- Eliminar Libro ---")
        id_libro = pedir_entero("  ID del libro a eliminar: ")
        self._svc_libro.eliminar(id_libro)
        print("\n  Libro eliminado correctamente "
              "(junto con sus precios y su stock).")

    # ==================================================================
    # Tipos de Cotización
    # ==================================================================

    def _menu_tipos_cotizacion(self) -> None:
        """Muestra el menú de tipos de cotización y ejecuta la opción."""
        while True:
            mostrar_titulo("TIPOS DE COTIZACIÓN")
            print("  1. Crear")
            print("  2. Listar")
            print("  3. Buscar por ID")
            print("  4. Modificar")
            print("  5. Eliminar")
            print("  0. Volver")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5"],
            )

            try:
                if opcion == "1":
                    self._crear_tipo_cotizacion()
                elif opcion == "2":
                    self._listar_tipos_cotizacion()
                elif opcion == "3":
                    self._buscar_tipo_cotizacion()
                elif opcion == "4":
                    self._modificar_tipo_cotizacion()
                elif opcion == "5":
                    self._eliminar_tipo_cotizacion()
                elif opcion == "0":
                    break
            except (ErrorServicio, ValidationError, ValueError) as e:
                print(f"\n  Error: {e}")
            pausar()

    def _crear_tipo_cotizacion(self) -> None:
        """Pide los datos y crea un tipo de cotización."""
        print("\n  --- Crear Tipo de Cotización ---")
        id_tipo = pedir_entero("  ID: ")
        nombre = pedir_texto("  Nombre: ")
        datos = TipoCotizacionInput(id_tipo=id_tipo, nombre=nombre)
        tipo = self._svc_tipo_cotizacion.crear(datos.id_tipo, datos.nombre)
        print(f"\n  Tipo creado: {tipo}")

    def _listar_tipos_cotizacion(self) -> None:
        """Lista tipos de cotización."""
        print("\n  --- Listado de Tipos de Cotización ---")
        tipos = self._svc_tipo_cotizacion.listar()
        if not tipos:
            print("  No hay tipos registrados.")
            return
        for t in tipos:
            print(f"  ID: {t.id_tipo} | {t.nombre}")

    def _buscar_tipo_cotizacion(self) -> None:
        """Busca un tipo de cotización por su ID y lo muestra."""
        print("\n  --- Buscar Tipo de Cotización ---")
        id_tipo = pedir_entero("  ID: ")
        tipo = self._svc_tipo_cotizacion.obtener(id_tipo)
        print(f"\n  ID: {tipo.id_tipo} | Nombre: {tipo.nombre}")

    def _modificar_tipo_cotizacion(self) -> None:
        """Pide los datos y modifica un tipo de cotización."""
        print("\n  --- Modificar Tipo de Cotización ---")
        id_tipo = pedir_entero("  ID del tipo a modificar: ")
        nuevo_nombre = pedir_texto("  Nuevo nombre: ")
        datos = TipoCotizacionUpdateInput(
            id_tipo=id_tipo, nuevo_nombre=nuevo_nombre,
        )
        tipo = self._svc_tipo_cotizacion.actualizar_nombre(
            datos.id_tipo, datos.nuevo_nombre,
        )
        print(f"\n  Tipo actualizado: {tipo}")

    def _eliminar_tipo_cotizacion(self) -> None:
        """Pide el ID y elimina un tipo de cotización."""
        print("\n  --- Eliminar Tipo de Cotización ---")
        id_tipo = pedir_entero("  ID del tipo a eliminar: ")
        self._svc_tipo_cotizacion.eliminar(id_tipo)
        print("\n  Tipo de cotización eliminado correctamente.")

    # ==================================================================
    # Cotizaciones del Dólar
    # ==================================================================

    def _menu_cotizaciones(self) -> None:
        """Muestra el menú de cotizaciones del dólar y ejecuta la opción."""
        while True:
            mostrar_titulo("COTIZACIONES DEL DÓLAR")
            print("  1. Registrar")
            print("  2. Consultar vigente")
            print("  3. Consultar histórico")
            print("  4. Modificar")
            print("  5. Eliminar")
            print("  0. Volver")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5"],
            )

            try:
                if opcion == "1":
                    self._registrar_cotizacion()
                elif opcion == "2":
                    self._cotizacion_vigente()
                elif opcion == "3":
                    self._historico_cotizacion()
                elif opcion == "4":
                    self._modificar_cotizacion()
                elif opcion == "5":
                    self._eliminar_cotizacion()
                elif opcion == "0":
                    break
            except (ErrorServicio, ValidationError, ValueError) as e:
                print(f"\n  Error: {e}")
            pausar()

    def _registrar_cotizacion(self) -> None:
        """Pide los datos y registra una cotización del dólar."""
        print("\n  --- Registrar Cotización ---")
        print("  Tipos disponibles:")
        for t in self._svc_tipo_cotizacion.listar():
            print(f"    ID: {t.id_tipo} | {t.nombre}")
        id_cotizacion = pedir_entero("  ID de la cotización: ")
        tipo_id = pedir_entero("  ID del tipo: ")
        valor_compra = pedir_float("  Valor de compra: ")
        valor_venta = pedir_float("  Valor de venta: ")
        fecha = pedir_fecha("  Fecha (AAAA-MM-DD): ")
        datos = CotizacionDolarInput(
            id_cotizacion=id_cotizacion, tipo_id=tipo_id,
            valor_compra=valor_compra, valor_venta=valor_venta,
            fecha=fecha,
        )
        cotizacion = self._svc_cotizacion.registrar(
            datos.id_cotizacion, datos.tipo_id,
            datos.valor_compra, datos.valor_venta, datos.fecha,
        )
        print(f"\n  Cotización registrada: {cotizacion}")

    def _cotizacion_vigente(self) -> None:
        """Muestra la cotización vigente de un tipo."""
        print("\n  --- Cotización Vigente ---")
        print("  Tipos disponibles:")
        for t in self._svc_tipo_cotizacion.listar():
            print(f"    ID: {t.id_tipo} | {t.nombre}")
        tipo_id = pedir_entero("  ID del tipo: ")
        cotizacion = self._svc_cotizacion.obtener_vigente(tipo_id)
        print(f"\n  {cotizacion}")

    def _historico_cotizacion(self) -> None:
        """Muestra el histórico de cotizaciones de un tipo."""
        print("\n  --- Histórico de Cotizaciones ---")
        print("  Tipos disponibles:")
        for t in self._svc_tipo_cotizacion.listar():
            print(f"    ID: {t.id_tipo} | {t.nombre}")
        tipo_id = pedir_entero("  ID del tipo: ")
        historico = self._svc_cotizacion.historico(tipo_id)
        if not historico:
            print("\n  No hay cotizaciones para ese tipo.")
            return
        for c in historico:
            print(f"  {c.fecha} | Compra: {c.valor_compra:.2f}"
                  f" | Venta: {c.valor_venta:.2f}")

    def _modificar_cotizacion(self) -> None:
        """Pide los datos y modifica una cotización del dólar."""
        print("\n  --- Modificar Cotización ---")
        print("  Tipos disponibles:")
        for t in self._svc_tipo_cotizacion.listar():
            print(f"    ID: {t.id_tipo} | {t.nombre}")
        tipo_id = pedir_entero("  ID del tipo: ")
        fecha = pedir_fecha("  Fecha de la cotización (AAAA-MM-DD): ")

        cotizacion = self._svc_cotizacion.historico(tipo_id)
        encontrada = None
        for c in cotizacion:
            if c.tipo.id_tipo == tipo_id and c.fecha == fecha:
                encontrada = c
                break

        if encontrada is None:
            print("\n  No se encontró cotización para ese tipo y fecha.")
            return

        print(f"  Actual → Compra: {encontrada.valor_compra:.2f}"
              f" | Venta: {encontrada.valor_venta:.2f}")
        nuevo_compra = pedir_float("  Nuevo valor de compra: ")
        nuevo_venta = pedir_float("  Nuevo valor de venta: ")
        datos = CotizacionDolarUpdateInput(
            tipo_id=tipo_id, fecha=fecha,
            nuevo_valor_compra=nuevo_compra,
            nuevo_valor_venta=nuevo_venta,
        )
        encontrada.valor_compra = datos.nuevo_valor_compra
        encontrada.valor_venta = datos.nuevo_valor_venta
        resultado = self._svc_cotizacion.actualizar(encontrada)
        print(f"\n  Cotización actualizada: {resultado}")

    def _eliminar_cotizacion(self) -> None:
        """Pide el ID y elimina una cotización del dólar."""
        print("\n  --- Eliminar Cotización ---")
        tipo_id = pedir_entero("  ID del tipo: ")
        fecha = pedir_fecha("  Fecha (AAAA-MM-DD): ")
        eliminada = self._svc_cotizacion.eliminar(tipo_id, fecha)
        if eliminada:
            print("\n  Cotización eliminada correctamente.")
        else:
            print("\n  No se encontró cotización para ese tipo y fecha.")

    # ==================================================================
    # Reportes de precios
    # ==================================================================

    def _obtener_cotizaciones_api(self) -> None:
        """Consulta la API del dólar y registra las cotizaciones obtenidas."""
        print("\n  --- Obtener Cotizaciones por API ---")
        tipos_previos = {t.nombre for t in self._svc_tipo_cotizacion.listar()}
        cotizaciones = self._svc_cotizacion.obtener_cotizaciones()

        print(f"\n  Cotizaciones registradas: {len(cotizaciones)}")
        for c in sorted(cotizaciones, key=lambda x: x.tipo.id_tipo):
            print(f"    {c.tipo.nombre:<12} compra {c.valor_compra:>10.2f}"
                  f" | venta {c.valor_venta:>10.2f} | {c.fecha}")

        nuevos = sorted({
            c.tipo.nombre for c in cotizaciones
        } - tipos_previos)
        if nuevos:
            print(f"\n  Tipos de cotización creados: {', '.join(nuevos)}")

        print("\n  Si un tipo ya tenía cotización para esa fecha, se actualizó"
              " en lugar de duplicarse.")

    def _elegir_cotizacion_usd(self) -> CotizacionDolar:
        """Pide al usuario el tipo de cotización que fija el valor del USD.

        Returns:
            CotizacionDolar: La cotización vigente del tipo elegido.

        Raises:
            EntidadNoEncontradaError: Si no hay cotizaciones registradas.
        """
        vigentes = self._svc_cotizacion.listar_vigentes()
        if not vigentes:
            raise EntidadNoEncontradaError(
                "No hay cotizaciones registradas. Use la opción 9 para "
                "obtenerlas por API."
            )

        por_defecto = next(
            (c for c in vigentes
             if c.tipo.nombre.lower() == TIPO_COTIZACION_OFICIAL.lower()),
            vigentes[0],
        )
        print("\n  Tipos de cotización con valor vigente:")
        for c in vigentes:
            print(f"    ID: {c.tipo.id_tipo} | {c.tipo.nombre:<10}"
                  f" venta {c.valor_venta:>10.2f} ({c.fecha})")

        por_id = {c.tipo.id_tipo: c for c in vigentes}
        while True:
            texto = pedir_texto(
                f"  ID del tipo para el USD [Enter = "
                f"{por_defecto.tipo.nombre}]: ",
                permitir_vacio=True,
            )
            if not texto:
                return por_defecto
            if texto.isdigit() and int(texto) in por_id:
                return por_id[int(texto)]
            print("  Error: elija uno de los IDs listados.")

    def _obtener_tasas(self, cotizacion_usd: CotizacionDolar
                       ) -> Dict[str, float]:
        """Arma las tasas de conversión a pesos de cada moneda.

        Las monedas distintas del dólar salen de la API de cotizaciones; el
        dólar usa el valor de venta del tipo elegido. Si la API no responde,
        solo quedan disponibles ARS y USD.

        Args:
            cotizacion_usd (CotizacionDolar): Cotización que fija el USD.

        Returns:
            Dict[str, float]: Pesos por unidad de cada moneda.
        """
        tasas: Dict[str, float] = {}
        try:
            tasas.update(self._svc_cotizacion.obtener_cotizaciones_monedas())
        except ErrorServicio as error:
            print(f"\n  Aviso: no se pudieron obtener las demás monedas "
                  f"({error}). Solo se convierte con USD.")
        tasas["USD"] = cotizacion_usd.valor_venta
        return tasas

    def _lista_precios_bimonetaria(self) -> None:
        """Muestra los precios del catálogo en pesos y en otra moneda."""
        print("\n  --- Lista de Precios Bimonetaria ---")
        monedas = self._svc_moneda.listar()
        print("  Monedas disponibles:")
        for m in monedas:
            print(f"    {m.codigo} – {m.nombre}")

        codigos = {m.codigo for m in monedas}
        codigo = pedir_texto(
            "  Código de la moneda a la que convertir: "
        ).upper()
        if codigo not in codigos:
            raise EntidadNoEncontradaError(
                f"No existe la moneda con código {codigo}"
            )

        cotizacion = self._elegir_cotizacion_usd()
        print(f"\n  Cotización del USD: {cotizacion.tipo.nombre}, "
              f"valor de venta {cotizacion.valor_venta:.2f} "
              f"({cotizacion.fecha})")
        tasas = self._obtener_tasas(cotizacion)

        if codigo not in tasas and codigo != MONEDA_BASE:
            print(f"  Aviso: no hay cotización para {codigo}; se muestran "
                  "como N/D los libros sin precio cargado en esa moneda.")

        print(f"\n  {'ID':>3} {'Libro':<30} {MONEDA_BASE:>14} "
              f"{codigo:>14}")
        for fila in self._svc_libro.listar_precios_bimonetarios(
            codigo, tasas
        ):
            ars = ("N/D" if fila.valor_ars is None
                   else f"{fila.valor_ars:,.2f}")
            destino = ("N/D" if fila.valor_destino is None
                       else f"{fila.valor_destino:,.2f}")
            print(f"  {fila.libro.id_libro:>3} {fila.libro.titulo[:30]:<30}"
                  f" {ars:>14} {destino:>14}")

    def _exportar_precios_csv(self) -> None:
        """Exporta los precios de todos los libros en todas las monedas."""
        print("\n  --- Exportar Precios a CSV ---")

        codigos = [m.codigo for m in self._svc_moneda.listar()]
        cotizacion = self._elegir_cotizacion_usd()
        tasas = self._obtener_tasas(cotizacion)
        filas = self._svc_libro.listar_precios_multimonetarios(
            codigos, tasas
        )

        os.makedirs(CARPETA_REPORTES, exist_ok=True)
        nombre = f"precios_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv"
        ruta = os.path.join(CARPETA_REPORTES, nombre)

        with open(ruta, mode="w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["libro_id", "isbn", "titulo", *codigos])
            for libro, valores in filas:
                escritor.writerow([
                    libro.id_libro,
                    libro.isbn,
                    libro.titulo,
                    *[
                        "" if valores[codigo] is None
                        else f"{valores[codigo]:.2f}"
                        for codigo in codigos
                    ],
                ])

        print(f"\n  Archivo generado: {os.path.abspath(ruta)}")
        print(f"  {len(filas)} libros exportados en {len(codigos)} monedas.")
        print(f"  USD valuado con {cotizacion.tipo.nombre} "
              f"(venta {cotizacion.valor_venta:.2f}).")
        print("  Las monedas sin cotización se exportan vacías.")

    # ==================================================================
    # Scraping de la competencia
    # ==================================================================

    @staticmethod
    def _ofrecer_descarga(ruta: str) -> None:
        """Muestra la ruta de un archivo y ofrece descargarlo en Colab.

        Args:
            ruta (str): Ruta del archivo generado.
        """
        print(f"\n  Archivo generado: {os.path.abspath(ruta)}")
        if archivos_colab is None:
            return
        if pedir_opcion("  ¿Descargar el archivo? (s/n): ", ["s", "n"]) == "s":
            archivos_colab.download(ruta)

    def _pedir_umbral(self) -> float:
        """Pide la diferencia de precio, en %, que dispara una alerta.

        Returns:
            float: Porcentaje mayor que cero.
        """
        while True:
            umbral = pedir_float(
                "  Diferencia de precio que genera alerta (en %): "
            )
            if umbral > 0:
                return umbral
            print("  Error: el porcentaje debe ser mayor que cero.")

    def _ejecutar_scraping(self) -> None:
        """Pide el umbral, ejecuta el scraper y muestra el resumen."""
        print("\n  --- Ejecutar Scraping (Cúspide) ---")
        umbral = self._pedir_umbral()

        print("\n  Buscando los libros del catálogo en Cúspide."
              " Puede demorar unos minutos...")
        resultado = self._svc_scraping.ejecutar(umbral)

        print(f"\n  Libros buscados:      {resultado.libros_buscados}")
        print(f"  Resultados guardados: {resultado.resultados}")
        print(f"  Coincidencias:        {resultado.coincidencias}")
        print(f"  Alertas (>= {umbral:g} %): {resultado.alertas}")
        self._ofrecer_descarga(resultado.ruta_alertas)
