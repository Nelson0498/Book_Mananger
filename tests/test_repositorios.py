"""Pruebas de los repositorios SQLAlchemy y su conversión a entidades."""

import datetime
import os
import unittest

from book_manager.entities.entities import Genero, Precio
from book_manager.repositories.repositories import (
    RepositorioGenero,
    RepositorioPrecioSQLAlchemy,
)

from tests import apoyo


class PruebaLecturas(unittest.TestCase):
    """Verifica las lecturas sobre los datos migrados."""

    def setUp(self) -> None:
        self.conexion = apoyo.crear_conexion_migrada()
        self.repos = apoyo.crear_repositorios(self.conexion)

    def tearDown(self) -> None:
        self.conexion.cerrar()

    def test_cada_repositorio_devuelve_sus_registros(self) -> None:
        self.assertEqual(len(self.repos.genero.leer_todos()), 10)
        self.assertEqual(len(self.repos.editorial.leer_todos()), 10)
        self.assertEqual(len(self.repos.moneda.leer_todos()), 10)
        self.assertEqual(len(self.repos.tipo_cotizacion.leer_todos()), 10)
        self.assertEqual(len(self.repos.precio.leer_todos()), 10)
        self.assertEqual(len(self.repos.libro.leer_todos()), 10)
        self.assertEqual(len(self.repos.stock.leer_todos()), 10)
        self.assertEqual(len(self.repos.cotizacion.leer_todos()), 10)

    def test_devuelve_entidades_de_dominio(self) -> None:
        genero = self.repos.genero.leer_por_id(1)
        self.assertIsInstance(genero, Genero)
        self.assertEqual(genero.nombre, "Ficción")

    def test_decimal_se_convierte_a_float(self) -> None:
        precio = self.repos.precio.leer_por_id(1)
        self.assertIsInstance(precio.valor, float)
        self.assertEqual(precio.valor, 15000.0)
        self.assertEqual(precio.moneda.codigo, "ARS")

    def test_reconstruye_las_relaciones_del_libro(self) -> None:
        libro = self.repos.libro.leer_por_isbn("978-950-731-001-1")

        self.assertEqual(libro.titulo, "Cien años de soledad")
        self.assertEqual(libro.editorial.nombre, "Planeta")
        self.assertEqual(libro.editorial.pais, "Argentina")
        self.assertEqual(libro.genero.nombre, "Ficción")
        self.assertEqual(libro.precio.moneda.codigo, "ARS")
        self.assertEqual(libro.stock.cantidad, 25)
        self.assertEqual(libro.stock.libro_isbn, libro.isbn)

    def test_busquedas_por_clave(self) -> None:
        self.assertIsNotNone(self.repos.stock.leer_por_libro("978-950-731-001-1"))
        self.assertIsNotNone(
            self.repos.cotizacion.leer_por_tipo_y_fecha(
                1, datetime.date(2024, 1, 15)
            )
        )
        self.assertEqual(
            len(self.repos.cotizacion.leer_historico_por_tipo(1)), 2
        )

    def test_devuelve_none_si_no_existe(self) -> None:
        self.assertIsNone(self.repos.genero.leer_por_id(999))
        self.assertIsNone(self.repos.libro.leer_por_isbn("inexistente"))
        self.assertIsNone(self.repos.stock.leer_por_libro("inexistente"))
        self.assertIsNone(
            self.repos.cotizacion.leer_por_tipo_y_fecha(
                1, datetime.date(2000, 1, 1)
            )
        )


class PruebaEscrituras(unittest.TestCase):
    """Verifica las altas, modificaciones y bajas."""

    def setUp(self) -> None:
        self.conexion = apoyo.crear_conexion_migrada()
        self.repos = apoyo.crear_repositorios(self.conexion)

    def tearDown(self) -> None:
        self.conexion.cerrar()

    def test_alta_modificacion_y_baja(self) -> None:
        self.repos.genero.crear(Genero(id_genero=99, nombre="Ensayo"))
        self.assertEqual(self.repos.genero.leer_por_id(99).nombre, "Ensayo")

        genero = self.repos.genero.leer_por_id(99)
        genero.nombre = "Ensayo literario"
        self.repos.genero.actualizar(genero)
        self.assertEqual(
            self.repos.genero.leer_por_id(99).nombre, "Ensayo literario"
        )

        self.assertTrue(self.repos.genero.eliminar(99))
        self.assertIsNone(self.repos.genero.leer_por_id(99))
        self.assertFalse(self.repos.genero.eliminar(99))

    def test_modificacion_de_precio_con_float(self) -> None:
        precio = self.repos.precio.leer_por_id(1)
        precio.valor = 29.99
        self.repos.precio.actualizar(precio)
        self.assertEqual(self.repos.precio.leer_por_id(1).valor, 29.99)

    def test_no_permite_ids_repetidos(self) -> None:
        with self.assertRaises(ValueError):
            self.repos.genero.crear(Genero(id_genero=1, nombre="Repetido"))

    def test_no_permite_actualizar_inexistentes(self) -> None:
        with self.assertRaises(ValueError):
            self.repos.genero.actualizar(Genero(id_genero=999, nombre="X"))

    def test_no_permite_libros_duplicados(self) -> None:
        libro = self.repos.libro.leer_por_isbn("978-950-731-001-1")
        with self.assertRaises(ValueError):
            self.repos.libro.crear(libro)

    def test_no_permite_stock_duplicado(self) -> None:
        stock = self.repos.stock.leer_por_libro("978-950-731-001-1")
        with self.assertRaises(ValueError):
            self.repos.stock.crear(stock)

    def test_no_permite_cotizaciones_duplicadas(self) -> None:
        cotizacion = self.repos.cotizacion.leer_por_tipo_y_fecha(
            1, datetime.date(2024, 1, 15)
        )
        with self.assertRaises(ValueError):
            self.repos.cotizacion.crear(cotizacion)

    def test_stock_requiere_isbn(self) -> None:
        from book_manager.entities.entities import Stock

        with self.assertRaises(ValueError):
            self.repos.stock.crear(Stock(id_stock=80, cantidad=1))

    def test_no_elimina_un_precio_asociado_a_un_libro(self) -> None:
        """La FK libros.precio_id es NOT NULL: se informa en lugar de fallar."""
        self.assertIsInstance(
            self.repos.precio, RepositorioPrecioSQLAlchemy
        )
        with self.assertRaises(ValueError):
            self.repos.precio.eliminar(1)

        self.assertIsNotNone(self.repos.precio.leer_por_id(1))

    def test_elimina_un_precio_sin_libro_asociado(self) -> None:
        self.repos.precio.crear(Precio(
            id_precio=95, valor=100.0,
            moneda=self.repos.moneda.leer_por_id(1),
        ))
        self.assertTrue(self.repos.precio.eliminar(95))
        self.assertIsNone(self.repos.precio.leer_por_id(95))


class PruebaCodificacionCsv(unittest.TestCase):
    """El repositorio CSV lee archivos con y sin BOM."""

    def test_lee_un_csv_guardado_con_bom(self) -> None:
        with apoyo.carpeta_temporal("repo_csv_bom") as carpeta:
            ruta = os.path.join(carpeta, "generos.csv")
            with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
                archivo.write("id,nombre\n1,Ficción\n2,Poesía\n")

            generos = RepositorioGenero(ruta_csv=ruta).leer_todos()

        self.assertEqual(len(generos), 2)
        self.assertEqual([g.nombre for g in generos], ["Ficción", "Poesía"])

    def test_lee_un_csv_sin_bom_con_ene(self) -> None:
        with apoyo.carpeta_temporal("repo_csv_utf8") as carpeta:
            ruta = os.path.join(carpeta, "generos.csv")
            with open(ruta, "w", encoding="utf-8", newline="") as archivo:
                archivo.write("id,nombre\n1,Ñandú\n")

            generos = RepositorioGenero(ruta_csv=ruta).leer_todos()

        self.assertEqual(generos[0].nombre, "Ñandú")


if __name__ == "__main__":
    unittest.main()
