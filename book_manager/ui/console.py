"""
Interfaz de consola (CLI) para el sistema Book Manager.

Presenta menús interactivos para realizar CRUD sobre todas las
entidades del sistema.  Toda la lógica de negocio se delega a
los servicios; la consola solo se encarga de pedir datos al
usuario, llamar al servicio correspondiente y mostrar resultados.
"""

import datetime
from typing import Optional

from book_manager.services.services import (
    EntidadNoEncontradaError,
    ErrorServicio,
    OperacionInvalidaError,
    ServicioCotizacionDolar,
    ServicioEditorial,
    ServicioGenero,
    ServicioLibro,
    ServicioMoneda,
    ServicioPrecio,
    ServicioStock,
    ServicioTipoCotizacion,
)
from pydantic import ValidationError
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
    PrecioUpdateInput,
    StockInput,
    StockMovimientoInput,
    TipoCotizacionInput,
    TipoCotizacionUpdateInput,
)


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
    ) -> None:
        self._svc_genero = svc_genero
        self._svc_editorial = svc_editorial
        self._svc_moneda = svc_moneda
        self._svc_tipo_cotizacion = svc_tipo_cotizacion
        self._svc_precio = svc_precio
        self._svc_stock = svc_stock
        self._svc_libro = svc_libro
        self._svc_cotizacion = svc_cotizacion

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
            print("  0. Salir")

            opcion = pedir_opcion(
                "\n  Seleccione una opción: ",
                ["0", "1", "2", "3", "4", "5", "6", "7", "8"],
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
            elif opcion == "0":
                print("\n  ¡Hasta luego!")
                break

    # ==================================================================
    # Géneros
    # ==================================================================

    def _menu_generos(self) -> None:
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
        print("\n  --- Crear Género ---")
        id_genero = pedir_entero("  ID: ")
        nombre = pedir_texto("  Nombre: ")
        datos = GeneroInput(id_genero=id_genero, nombre=nombre)
        genero = self._svc_genero.crear(datos.id_genero, datos.nombre)
        print(f"\n  Género creado: {genero}")

    def _listar_generos(self) -> None:
        print("\n  --- Listado de Géneros ---")
        generos = self._svc_genero.listar()
        if not generos:
            print("  No hay géneros registrados.")
            return
        for g in generos:
            print(f"  ID: {g.id_genero} | Nombre: {g.nombre}")

    def _buscar_genero(self) -> None:
        print("\n  --- Buscar Género ---")
        id_genero = pedir_entero("  ID: ")
        genero = self._svc_genero.obtener(id_genero)
        print(f"\n  ID: {genero.id_genero} | Nombre: {genero.nombre}")

    def _modificar_genero(self) -> None:
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
        print("\n  --- Eliminar Género ---")
        id_genero = pedir_entero("  ID del género a eliminar: ")
        self._svc_genero.eliminar(id_genero)
        print("\n  Género eliminado correctamente.")

    # ==================================================================
    # Editoriales
    # ==================================================================

    def _menu_editoriales(self) -> None:
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
        print("\n  --- Listado de Editoriales ---")
        editoriales = self._svc_editorial.listar()
        if not editoriales:
            print("  No hay editoriales registradas.")
            return
        for e in editoriales:
            pais = e.pais or "N/D"
            print(f"  ID: {e.id_editorial} | {e.nombre} | País: {pais}")

    def _buscar_editorial(self) -> None:
        print("\n  --- Buscar Editorial ---")
        id_editorial = pedir_entero("  ID: ")
        editorial = self._svc_editorial.obtener(id_editorial)
        pais = editorial.pais or "N/D"
        print(f"\n  ID: {editorial.id_editorial} | {editorial.nombre}"
              f" | País: {pais}")

    def _modificar_editorial(self) -> None:
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
        print("\n  --- Eliminar Editorial ---")
        id_editorial = pedir_entero("  ID de la editorial a eliminar: ")
        self._svc_editorial.eliminar(id_editorial)
        print("\n  Editorial eliminada correctamente.")

    # ==================================================================
    # Monedas
    # ==================================================================

    def _menu_monedas(self) -> None:
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
        print("\n  --- Listado de Monedas ---")
        monedas = self._svc_moneda.listar()
        if not monedas:
            print("  No hay monedas registradas.")
            return
        for m in monedas:
            print(f"  ID: {m.id_moneda} | {m.codigo} | {m.nombre}"
                  f" | {m.simbolo}")

    def _buscar_moneda(self) -> None:
        print("\n  --- Buscar Moneda ---")
        id_moneda = pedir_entero("  ID: ")
        moneda = self._svc_moneda.obtener(id_moneda)
        print(f"\n  ID: {moneda.id_moneda} | {moneda.codigo}"
              f" | {moneda.nombre} | {moneda.simbolo}")

    def _modificar_moneda(self) -> None:
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
        print("\n  --- Eliminar Moneda ---")
        id_moneda = pedir_entero("  ID de la moneda a eliminar: ")
        self._svc_moneda.eliminar(id_moneda)
        print("\n  Moneda eliminada correctamente.")

    # ==================================================================
    # Precios
    # ==================================================================

    def _menu_precios(self) -> None:
        while True:
            mostrar_titulo("PRECIOS")
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
                    self._crear_precio()
                elif opcion == "2":
                    self._listar_precios()
                elif opcion == "3":
                    self._buscar_precio()
                elif opcion == "4":
                    self._modificar_precio()
                elif opcion == "5":
                    self._eliminar_precio()
                elif opcion == "0":
                    break
            except (ErrorServicio, ValidationError, ValueError) as e:
                print(f"\n  Error: {e}")
            pausar()

    def _crear_precio(self) -> None:
        print("\n  --- Crear Precio ---")
        print("  Monedas disponibles:")
        for m in self._svc_moneda.listar():
            print(f"    ID: {m.id_moneda} | {m.codigo} – {m.nombre}")
        id_precio = pedir_entero("  ID del precio: ")
        valor = pedir_float("  Valor: ")
        moneda_id = pedir_entero("  ID de la moneda: ")
        datos = PrecioInput(
            id_precio=id_precio, valor=valor, moneda_id=moneda_id,
        )
        precio = self._svc_precio.crear(
            datos.id_precio, datos.valor, datos.moneda_id,
        )
        print(f"\n  Precio creado: {precio}")

    def _listar_precios(self) -> None:
        print("\n  --- Listado de Precios ---")
        precios = self._svc_precio.listar()
        if not precios:
            print("  No hay precios registrados.")
            return
        for p in precios:
            print(f"  ID: {p.id_precio} | {p.valor:.2f}"
                  f" {p.moneda.codigo}")

    def _buscar_precio(self) -> None:
        print("\n  --- Buscar Precio ---")
        id_precio = pedir_entero("  ID: ")
        precio = self._svc_precio.obtener(id_precio)
        print(f"\n  ID: {precio.id_precio} | {precio.valor:.2f}"
              f" {precio.moneda.codigo} ({precio.moneda.nombre})")

    def _modificar_precio(self) -> None:
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
        print("\n  --- Eliminar Precio ---")
        id_precio = pedir_entero("  ID del precio a eliminar: ")
        self._svc_precio.eliminar(id_precio)
        print("\n  Precio eliminado correctamente.")

    # ==================================================================
    # Stock
    # ==================================================================

    def _menu_stock(self) -> None:
        while True:
            mostrar_titulo("STOCK")
            print("  1. Crear")
            print("  2. Consultar por ISBN")
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
        print("\n  --- Crear Stock ---")
        id_stock = pedir_entero("  ID del stock: ")
        isbn = pedir_texto("  ISBN del libro: ")
        cantidad = pedir_entero("  Cantidad inicial: ")
        cantidad_minima = pedir_entero("  Cantidad mínima: ")
        datos = StockInput(
            id_stock=id_stock, libro_isbn=isbn,
            cantidad=cantidad, cantidad_minima=cantidad_minima,
        )
        stock = self._svc_stock.crear(
            datos.id_stock, datos.libro_isbn,
            datos.cantidad, datos.cantidad_minima,
        )
        print(f"\n  Stock creado: {stock}")

    def _consultar_stock(self) -> None:
        print("\n  --- Consultar Stock ---")
        isbn = pedir_texto("  ISBN del libro: ")
        stock = self._svc_stock.obtener(isbn)
        print(f"\n  ISBN: {stock.libro_isbn}")
        print(f"  Cantidad: {stock.cantidad}")
        print(f"  Cantidad mínima: {stock.cantidad_minima}")
        print(f"  Stock bajo: {'Sí' if stock.hay_stock_bajo() else 'No'}")

    def _listar_stocks(self) -> None:
        print("\n  --- Listado de Stock ---")
        stocks = self._svc_stock.listar()
        if not stocks:
            print("  No hay stocks registrados.")
            return
        for s in stocks:
            alerta = " ⚠ BAJO" if s.hay_stock_bajo() else ""
            print(f"  ISBN: {s.libro_isbn} | Cant: {s.cantidad}"
                  f" | Min: {s.cantidad_minima}{alerta}")

    def _registrar_ingreso(self) -> None:
        print("\n  --- Registrar Ingreso ---")
        isbn = pedir_texto("  ISBN del libro: ")
        cantidad = pedir_entero("  Cantidad a ingresar: ")
        datos = StockMovimientoInput(libro_isbn=isbn, cantidad=cantidad)
        stock = self._svc_stock.registrar_ingreso(
            datos.libro_isbn, datos.cantidad,
        )
        print(f"\n  Ingreso registrado. Stock actual: {stock.cantidad}")

    def _registrar_egreso(self) -> None:
        print("\n  --- Registrar Egreso ---")
        isbn = pedir_texto("  ISBN del libro: ")
        cantidad = pedir_entero("  Cantidad a retirar: ")
        datos = StockMovimientoInput(libro_isbn=isbn, cantidad=cantidad)
        stock = self._svc_stock.registrar_egreso(
            datos.libro_isbn, datos.cantidad,
        )
        print(f"\n  Egreso registrado. Stock actual: {stock.cantidad}")

    def _alerta_stock_bajo(self) -> None:
        print("\n  --- Alerta de Stock Bajo ---")
        isbn = pedir_texto("  ISBN del libro: ")
        alerta = self._svc_stock.hay_alerta_stock_bajo(isbn)
        if alerta:
            print("\n  ⚠ ALERTA: el stock está bajo el mínimo.")
        else:
            print("\n  El stock está dentro de los niveles normales.")

    def _eliminar_stock(self) -> None:
        print("\n  --- Eliminar Stock ---")
        isbn = pedir_texto("  ISBN del libro: ")
        eliminado = self._svc_stock.eliminar(isbn)
        if eliminado:
            print("\n  Stock eliminado correctamente.")
        else:
            print("\n  No se encontró stock para ese ISBN.")

    # ==================================================================
    # Libros
    # ==================================================================

    def _menu_libros(self) -> None:
        while True:
            mostrar_titulo("LIBROS")
            print("  1. Crear")
            print("  2. Listar")
            print("  3. Buscar por ISBN")
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

    def _crear_libro(self) -> None:
        print("\n  --- Crear Libro ---")

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

        print("\n  Monedas disponibles:")
        for m in self._svc_moneda.listar():
            print(f"    ID: {m.id_moneda} | {m.codigo} – {m.nombre}")
        moneda_id = pedir_entero("  ID de la moneda: ")

        precio_id = pedir_entero("  ID para el nuevo precio: ")
        precio_valor = pedir_float("  Valor del precio: ")

        stock_id = pedir_entero("  ID para el stock: ")
        cantidad_inicial = pedir_entero("  Cantidad inicial de stock: ")
        cantidad_minima = pedir_entero("  Cantidad mínima de stock: ")

        datos = LibroInput(
            isbn=isbn, titulo=titulo, autor=autor,
            editorial_id=editorial_id, genero_id=genero_id,
            precio_id=precio_id, precio_valor=precio_valor,
            moneda_id=moneda_id,
            stock_id=stock_id, cantidad_inicial=cantidad_inicial,
            cantidad_minima=cantidad_minima,
        )

        libro = self._svc_libro.crear(
            isbn=datos.isbn, titulo=datos.titulo, autor=datos.autor,
            editorial_id=datos.editorial_id, genero_id=datos.genero_id,
            precio_id=datos.precio_id, precio_valor=datos.precio_valor,
            moneda_id=datos.moneda_id,
            stock_id=datos.stock_id,
            cantidad_inicial=datos.cantidad_inicial,
            cantidad_minima=datos.cantidad_minima,
        )
        print(f"\n  Libro creado: {libro}")

    def _listar_libros(self) -> None:
        print("\n  --- Listado de Libros ---")
        libros = self._svc_libro.listar()
        if not libros:
            print("  No hay libros registrados.")
            return
        for libro in libros:
            print(f"  ISBN: {libro.isbn} | {libro.titulo}"
                  f" | {libro.autor}"
                  f" | {libro.precio}"
                  f" | Stock: {libro.stock.cantidad}")

    def _buscar_libro(self) -> None:
        print("\n  --- Buscar Libro ---")
        isbn = pedir_texto("  ISBN: ")
        libro = self._svc_libro.obtener(isbn)
        print(f"\n  ISBN:      {libro.isbn}")
        print(f"  Título:    {libro.titulo}")
        print(f"  Autor:     {libro.autor}")
        print(f"  Editorial: {libro.editorial.nombre}")
        print(f"  Género:    {libro.genero.nombre}")
        print(f"  Precio:    {libro.precio}")
        print(f"  Stock:     {libro.stock.cantidad} "
              f"(mín: {libro.stock.cantidad_minima})")

    def _modificar_libro(self) -> None:
        print("\n  --- Modificar Libro ---")
        isbn = pedir_texto("  ISBN del libro a modificar: ")
        print("  (Deje vacío para no modificar)")
        titulo = pedir_texto_opcional("  Nuevo título: ")
        autor = pedir_texto_opcional("  Nuevo autor: ")
        datos = LibroUpdateInput(isbn=isbn, titulo=titulo, autor=autor)
        libro = self._svc_libro.actualizar_datos(
            datos.isbn, titulo=datos.titulo, autor=datos.autor,
        )
        print(f"\n  Libro actualizado: {libro}")

    def _modificar_precio_libro(self) -> None:
        print("\n  --- Modificar Precio del Libro ---")
        isbn = pedir_texto("  ISBN del libro: ")
        nuevo_valor = pedir_float("  Nuevo valor del precio: ")
        datos = LibroPrecioUpdateInput(isbn=isbn, nuevo_valor=nuevo_valor)
        libro = self._svc_libro.actualizar_precio(
            datos.isbn, datos.nuevo_valor,
        )
        print(f"\n  Precio actualizado: {libro.precio}")

    def _eliminar_libro(self) -> None:
        print("\n  --- Eliminar Libro ---")
        isbn = pedir_texto("  ISBN del libro a eliminar: ")
        self._svc_libro.eliminar(isbn)
        print("\n  Libro eliminado correctamente "
              "(junto con su precio y stock).")

    # ==================================================================
    # Tipos de Cotización
    # ==================================================================

    def _menu_tipos_cotizacion(self) -> None:
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
        print("\n  --- Crear Tipo de Cotización ---")
        id_tipo = pedir_entero("  ID: ")
        nombre = pedir_texto("  Nombre: ")
        datos = TipoCotizacionInput(id_tipo=id_tipo, nombre=nombre)
        tipo = self._svc_tipo_cotizacion.crear(datos.id_tipo, datos.nombre)
        print(f"\n  Tipo creado: {tipo}")

    def _listar_tipos_cotizacion(self) -> None:
        print("\n  --- Listado de Tipos de Cotización ---")
        tipos = self._svc_tipo_cotizacion.listar()
        if not tipos:
            print("  No hay tipos registrados.")
            return
        for t in tipos:
            print(f"  ID: {t.id_tipo} | {t.nombre}")

    def _buscar_tipo_cotizacion(self) -> None:
        print("\n  --- Buscar Tipo de Cotización ---")
        id_tipo = pedir_entero("  ID: ")
        tipo = self._svc_tipo_cotizacion.obtener(id_tipo)
        print(f"\n  ID: {tipo.id_tipo} | Nombre: {tipo.nombre}")

    def _modificar_tipo_cotizacion(self) -> None:
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
        print("\n  --- Eliminar Tipo de Cotización ---")
        id_tipo = pedir_entero("  ID del tipo a eliminar: ")
        self._svc_tipo_cotizacion.eliminar(id_tipo)
        print("\n  Tipo de cotización eliminado correctamente.")

    # ==================================================================
    # Cotizaciones del Dólar
    # ==================================================================

    def _menu_cotizaciones(self) -> None:
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
        print("\n  --- Cotización Vigente ---")
        print("  Tipos disponibles:")
        for t in self._svc_tipo_cotizacion.listar():
            print(f"    ID: {t.id_tipo} | {t.nombre}")
        tipo_id = pedir_entero("  ID del tipo: ")
        cotizacion = self._svc_cotizacion.obtener_vigente(tipo_id)
        print(f"\n  {cotizacion}")

    def _historico_cotizacion(self) -> None:
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
        print("\n  --- Eliminar Cotización ---")
        tipo_id = pedir_entero("  ID del tipo: ")
        fecha = pedir_fecha("  Fecha (AAAA-MM-DD): ")
        eliminada = self._svc_cotizacion.eliminar(tipo_id, fecha)
        if eliminada:
            print("\n  Cotización eliminada correctamente.")
        else:
            print("\n  No se encontró cotización para ese tipo y fecha.")
