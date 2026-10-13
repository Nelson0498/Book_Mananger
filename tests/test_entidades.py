"""Pruebas de las validaciones de las entidades de dominio.

Cubren las validaciones incorporadas en los setters, los casos válidos, los
valores límite y las validaciones que ya existían antes de esta corrección.
"""

import unittest
from datetime import date

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


def crear_moneda() -> Moneda:
    """Devuelve una moneda válida para usar en las pruebas."""
    return Moneda(
        id_moneda=1, codigo="ARS", nombre="Peso Argentino", simbolo="$"
    )


def crear_libro() -> Libro:
    """Devuelve un libro válido con todas sus relaciones."""
    return Libro(
        isbn="978-950-731-001-1",
        titulo="Cien años de soledad",
        autor="Gabriel García Márquez",
        editorial=Editorial(
            id_editorial=1, nombre="Sudamericana", pais="Argentina"
        ),
        genero=Genero(id_genero=1, nombre="Ficción"),
        precio=Precio(id_precio=1, valor=15000.0, moneda=crear_moneda()),
        stock=Stock(
            id_stock=1, cantidad=25, cantidad_minima=5,
            libro_isbn="978-950-731-001-1",
        ),
    )


class PruebaValidacionesDeMoneda(unittest.TestCase):
    """Validaciones de Moneda."""

    def setUp(self) -> None:
        self.moneda = crear_moneda()

    def test_nombre_vacio_es_rechazado(self) -> None:
        with self.assertRaises(ValueError):
            self.moneda.nombre = ""

    def test_simbolo_vacio_es_rechazado(self) -> None:
        with self.assertRaises(ValueError):
            self.moneda.simbolo = ""

    def test_asigna_valores_validos(self) -> None:
        self.moneda.nombre = "Dólar Estadounidense"
        self.moneda.simbolo = "US$"

        self.assertEqual(self.moneda.nombre, "Dólar Estadounidense")
        self.assertEqual(self.moneda.simbolo, "US$")

    def test_nombre_con_solo_espacios_es_rechazado(self) -> None:
        for valor in (" ", "    ", "\t", " \t "):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ValueError):
                    self.moneda.nombre = valor

    def test_simbolo_con_solo_espacios_es_rechazado(self) -> None:
        for valor in (" ", "    ", "\t", " \t "):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ValueError):
                    self.moneda.simbolo = valor

    def test_conserva_el_valor_sin_modificarlo(self) -> None:
        """La validación usa `strip()`, pero no altera el valor almacenado."""
        self.moneda.nombre = " Peso Argentino "
        self.moneda.simbolo = " $ "

        self.assertEqual(self.moneda.nombre, " Peso Argentino ")
        self.assertEqual(self.moneda.simbolo, " $ ")

    def test_valor_limite_de_un_caracter_es_valido(self) -> None:
        self.moneda.nombre = "$"
        self.moneda.simbolo = "$"

        self.assertEqual(self.moneda.nombre, "$")
        self.assertEqual(self.moneda.simbolo, "$")

    def test_codigo_vacio_sigue_rechazandose(self) -> None:
        with self.assertRaises(ValueError):
            self.moneda.codigo = ""


class PruebaValidacionesDePrecio(unittest.TestCase):
    """Validaciones de Precio."""

    def setUp(self) -> None:
        self.precio = Precio(id_precio=1, valor=100.0, moneda=crear_moneda())

    def test_moneda_none_es_rechazada(self) -> None:
        with self.assertRaises(ValueError):
            self.precio.moneda = None

    def test_objeto_que_no_es_moneda_es_rechazado(self) -> None:
        with self.assertRaises(ValueError):
            self.precio.moneda = "ARS"

    def test_asigna_una_moneda_valida(self) -> None:
        otra = Moneda(
            id_moneda=2, codigo="USD", nombre="Dólar", simbolo="US$"
        )
        self.precio.moneda = otra

        self.assertIs(self.precio.moneda, otra)
        self.assertEqual(self.precio.moneda.codigo, "USD")

    def test_valor_negativo_sigue_rechazandose(self) -> None:
        with self.assertRaises(ValueError):
            self.precio.valor = -0.01

    def test_valor_cero_es_valido(self) -> None:
        self.precio.valor = 0.0
        self.assertEqual(self.precio.valor, 0.0)


class PruebaValidacionesDeStock(unittest.TestCase):
    """Validaciones de Stock."""

    def setUp(self) -> None:
        self.stock = Stock(
            id_stock=1, cantidad=10, cantidad_minima=2,
            libro_isbn="978-950-731-001-1",
        )

    def test_libro_isbn_vacio_es_rechazado(self) -> None:
        with self.assertRaises(ValueError):
            self.stock.libro_isbn = ""

    def test_libro_isbn_none_es_rechazado(self) -> None:
        with self.assertRaises(ValueError):
            self.stock.libro_isbn = None

    def test_libro_isbn_con_solo_espacios_es_rechazado(self) -> None:
        for valor in (" ", "    ", "\t", " \t "):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ValueError):
                    self.stock.libro_isbn = valor

    def test_cantidad_minima_negativa_es_rechazada(self) -> None:
        with self.assertRaises(ValueError):
            self.stock.cantidad_minima = -1

    def test_cantidad_minima_cero_es_valida(self) -> None:
        """Valor límite: el umbral de reposición puede ser cero."""
        self.stock.cantidad_minima = 0
        self.assertEqual(self.stock.cantidad_minima, 0)

    def test_asigna_valores_validos(self) -> None:
        self.stock.libro_isbn = "978-84-204-8311-5"
        self.stock.cantidad_minima = 7

        self.assertEqual(self.stock.libro_isbn, "978-84-204-8311-5")
        self.assertEqual(self.stock.cantidad_minima, 7)

    def test_libro_isbn_valido_sin_stock_bajo(self) -> None:
        self.stock.cantidad_minima = 10
        self.assertTrue(self.stock.hay_stock_bajo())

    def test_cantidad_negativa_sigue_rechazandose(self) -> None:
        with self.assertRaises(ValueError):
            self.stock.cantidad = -1


class PruebaValidacionesDeLibro(unittest.TestCase):
    """Validaciones de Libro."""

    def setUp(self) -> None:
        self.libro = crear_libro()

    def test_autor_vacio_es_rechazado(self) -> None:
        with self.assertRaises(ValueError):
            self.libro.autor = ""

    def test_autor_con_solo_espacios_es_rechazado(self) -> None:
        for valor in (" ", "    ", "\t", " \t "):
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(ValueError):
                    self.libro.autor = valor

    def test_relaciones_none_son_rechazadas(self) -> None:
        with self.assertRaises(ValueError):
            self.libro.editorial = None
        with self.assertRaises(ValueError):
            self.libro.genero = None
        with self.assertRaises(ValueError):
            self.libro.precio = None
        with self.assertRaises(ValueError):
            self.libro.stock = None

    def test_relaciones_de_tipo_incorrecto_son_rechazadas(self) -> None:
        with self.assertRaises(ValueError):
            self.libro.editorial = "Planeta"
        with self.assertRaises(ValueError):
            self.libro.genero = 1
        with self.assertRaises(ValueError):
            self.libro.precio = 15000.0
        with self.assertRaises(ValueError):
            self.libro.stock = 25

    def test_asigna_relaciones_validas(self) -> None:
        editorial = Editorial(id_editorial=2, nombre="Planeta")
        genero = Genero(id_genero=2, nombre="Ensayo")
        precio = Precio(id_precio=2, valor=999.99, moneda=crear_moneda())
        stock = Stock(
            id_stock=2, cantidad=3, cantidad_minima=0,
            libro_isbn=self.libro.isbn,
        )

        self.libro.autor = "Otro autor"
        self.libro.editorial = editorial
        self.libro.genero = genero
        self.libro.precio = precio
        self.libro.stock = stock

        self.assertEqual(self.libro.autor, "Otro autor")
        self.assertIs(self.libro.editorial, editorial)
        self.assertIs(self.libro.genero, genero)
        self.assertIs(self.libro.precio, precio)
        self.assertIs(self.libro.stock, stock)

    def test_titulo_vacio_sigue_rechazandose(self) -> None:
        with self.assertRaises(ValueError):
            self.libro.titulo = ""


class PruebaConstruccionSinCambios(unittest.TestCase):
    """Los constructores siguen aceptando los mismos datos que antes."""

    def test_libro_completo_con_valores_por_defecto(self) -> None:
        libro = crear_libro()

        self.assertEqual(libro.isbn, "978-950-731-001-1")
        self.assertEqual(libro.stock.cantidad, 25)
        self.assertEqual(libro.precio.valor, 15000.0)

    def test_stock_acepta_los_valores_por_defecto(self) -> None:
        stock = Stock(id_stock=0, cantidad=0)

        self.assertEqual(stock.cantidad_minima, 0)
        self.assertIsNone(stock.libro_isbn)

    def test_las_validaciones_del_constructor_siguen_activas(self) -> None:
        with self.assertRaises(ValueError):
            Libro(
                isbn="", titulo="t", autor="a",
                editorial=Editorial(1, "E"), genero=Genero(1, "G"),
                precio=Precio(1, 1.0, crear_moneda()),
                stock=Stock(1, 1),
            )
        with self.assertRaises(ValueError):
            Libro(
                isbn="i", titulo="", autor="a",
                editorial=Editorial(1, "E"), genero=Genero(1, "G"),
                precio=Precio(1, 1.0, crear_moneda()),
                stock=Stock(1, 1),
            )

    def test_cotizacion_sigue_validando_compra_y_venta(self) -> None:
        tipo = TipoCotizacion(id_tipo=1, nombre="Oficial")
        cotizacion = CotizacionDolar(
            id_cotizacion=1, tipo=tipo, valor_compra=900.0,
            valor_venta=950.0, fecha=date(2024, 1, 15),
        )

        self.assertEqual(cotizacion.valor_compra, 900.0)
        with self.assertRaises(ValueError):
            cotizacion.valor_venta = -1.0


if __name__ == "__main__":
    unittest.main()
