"""Pruebas de la lógica de negocio operando sobre la base de datos."""

import unittest

from book_manager.services.services import (
    EntidadNoEncontradaError,
    OperacionInvalidaError,
)

from tests import apoyo


class PruebaServiciosSobreLaBase(unittest.TestCase):
    """Verifica que los servicios del Sprint 1 operen sobre SQLAlchemy."""

    def setUp(self) -> None:
        self.conexion = apoyo.crear_conexion_migrada()
        self.repos = apoyo.crear_repositorios(self.conexion)
        servicios = apoyo.crear_servicios(self.conexion)

        self.svc_genero = servicios.genero
        self.svc_editorial = servicios.editorial
        self.svc_moneda = servicios.moneda
        self.svc_tipo = servicios.tipo_cotizacion
        self.svc_precio = servicios.precio
        self.svc_stock = servicios.stock
        self.svc_libro = servicios.libro
        self.svc_cotizacion = servicios.cotizacion

    def tearDown(self) -> None:
        self.conexion.cerrar()

    def _crear_libro_de_prueba(self) -> None:
        self.svc_libro.crear(
            isbn="978-0000-0000-9", titulo="Libro de Prueba",
            autor="Autora de Prueba", editorial_id=1, genero_id=1,
            precio_id=50, precio_valor=1234.56, moneda_id=1, stock_id=50,
            cantidad_inicial=7, cantidad_minima=2,
        )

    def test_listado_de_libros(self) -> None:
        self.assertEqual(len(self.svc_libro.listar()), 10)

    def test_alta_completa_de_un_libro(self) -> None:
        self._crear_libro_de_prueba()

        libro = self.svc_libro.obtener("978-0000-0000-9")
        self.assertEqual(libro.stock.cantidad, 7)
        self.assertEqual(libro.precio.valor, 1234.56)
        self.assertEqual(len(self.svc_libro.listar()), 11)

    def test_el_libro_devuelto_incluye_el_stock_persistido(self) -> None:
        """Regresión: el libro devuelto por crear() no debe traer stock vacío.

        Como el stock se persiste después del libro (por la clave foránea
        stock.libro_isbn), el objeto devuelto debe releerse para reflejar el
        stock real en lugar del provisorio usado para construirlo.
        """
        devuelto = self.svc_libro.crear(
            isbn="978-0000-0000-7", titulo="Libro de Regresión",
            autor="Autora de Prueba", editorial_id=1, genero_id=1,
            precio_id=70, precio_valor=500.0, moneda_id=1, stock_id=70,
            cantidad_inicial=9, cantidad_minima=3,
        )
        obtenido = self.svc_libro.obtener("978-0000-0000-7")

        self.assertEqual(devuelto.stock.id_stock, obtenido.stock.id_stock)
        self.assertEqual(devuelto.stock.cantidad, obtenido.stock.cantidad)
        self.assertEqual(
            devuelto.stock.cantidad_minima, obtenido.stock.cantidad_minima
        )
        self.assertEqual(devuelto.stock.libro_isbn, obtenido.stock.libro_isbn)
        self.assertEqual(devuelto.stock.id_stock, 70)
        self.assertEqual(devuelto.stock.cantidad, 9)
        self.assertEqual(devuelto.isbn, obtenido.isbn)
        self.assertEqual(devuelto.precio.valor, obtenido.precio.valor)

    def test_movimientos_de_stock(self) -> None:
        self._crear_libro_de_prueba()

        self.assertEqual(
            self.svc_stock.registrar_ingreso("978-0000-0000-9", 5).cantidad, 12
        )
        self.assertEqual(
            self.svc_stock.registrar_egreso("978-0000-0000-9", 2).cantidad, 10
        )
        self.assertFalse(
            self.svc_stock.hay_alerta_stock_bajo("978-0000-0000-9")
        )

    def test_cotizacion_vigente_e_historico(self) -> None:
        vigente = self.svc_cotizacion.obtener_vigente(1)

        self.assertEqual(vigente.fecha.isoformat(), "2024-02-15")
        self.assertEqual(vigente.valor_venta, 970.0)
        self.assertEqual(len(self.svc_cotizacion.historico(1)), 2)

    def test_conversion_existente_del_sprint_1(self) -> None:
        """`cotizar_en` mantiene la regla del Sprint 1.

        Para pasar de ARS a USD usa el valor de *compra*, a diferencia del
        reporte bimonetario, que usa el valor de venta según la regla acordada.
        """
        vigente = self.svc_cotizacion.obtener_vigente(1)

        self.assertEqual(
            self.svc_libro.cotizar_en("978-950-731-001-1", vigente), 16.3
        )
        self.assertEqual(
            self.svc_libro.cotizar_en("978-84-204-8311-5", vigente), 29090.3
        )

    def test_alta_rechaza_genero_inexistente(self) -> None:
        with self.assertRaises(EntidadNoEncontradaError):
            self.svc_libro.crear(
                isbn="978-0000-0000-8", titulo="X", autor="Y",
                editorial_id=1, genero_id=999, precio_id=60,
                precio_valor=1.0, moneda_id=1, stock_id=60,
            )

    def test_no_elimina_un_genero_con_libros(self) -> None:
        with self.assertRaises(OperacionInvalidaError):
            self.svc_genero.eliminar(1)

    def test_no_permite_monedas_duplicadas(self) -> None:
        with self.assertRaises(OperacionInvalidaError):
            self.svc_moneda.crear(1, "ARS", "Peso Argentino", "$")

    def test_eliminar_libro_borra_stock_y_precio(self) -> None:
        """El orden de baja respeta la clave foránea libros.precio_id."""
        self._crear_libro_de_prueba()

        self.assertTrue(self.svc_libro.eliminar("978-0000-0000-9"))
        self.assertEqual(len(self.svc_libro.listar()), 10)

        with self.assertRaises(EntidadNoEncontradaError):
            self.svc_stock.obtener("978-0000-0000-9")
        with self.assertRaises(EntidadNoEncontradaError):
            self.svc_precio.obtener(50)

    def test_alta_y_baja_de_genero_sin_libros(self) -> None:
        self.svc_genero.crear(77, "Ensayo")
        self.assertEqual(self.svc_genero.obtener(77).nombre, "Ensayo")
        self.assertTrue(self.svc_genero.eliminar(77))


if __name__ == "__main__":
    unittest.main()
