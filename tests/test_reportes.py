"""Pruebas de los reportes: conversión bimonetaria y exportación a CSV."""

import csv
import io
import os
import unittest
from contextlib import redirect_stdout
from unittest import mock

from book_manager.services.services import TIPO_COTIZACION_OFICIAL
from book_manager.ui import console as consola_mod

from tests import apoyo

ISBN_PESOS = "978-950-731-001-1"      # 15000.00 ARS
ISBN_DOLARES = "978-84-204-8311-5"    # 29.99 USD


class PruebaConversionBimonetaria(unittest.TestCase):
    """Verifica la regla aprobada: cotización Oficial, valor de venta."""

    def setUp(self) -> None:
        self.conexion = apoyo.crear_conexion_migrada()
        self.addCleanup(self.conexion.cerrar)
        self.servicios = apoyo.crear_servicios(self.conexion)
        self.cotizacion = (
            self.servicios.cotizacion.obtener_vigente_por_nombre(
                TIPO_COTIZACION_OFICIAL
            )
        )

    def _filas(self, moneda: str) -> dict:
        return {
            fila.libro.isbn: fila
            for fila in self.servicios.libro.listar_precios_bimonetarios(
                self.cotizacion, moneda
            )
        }

    def test_usa_la_cotizacion_oficial_vigente(self) -> None:
        self.assertEqual(self.cotizacion.tipo.nombre, "Oficial")
        self.assertEqual(self.cotizacion.valor_venta, 970.0)
        self.assertEqual(self.cotizacion.fecha.isoformat(), "2024-02-15")

    def test_convierte_pesos_a_dolares_con_el_valor_de_venta(self) -> None:
        fila = self._filas("USD")[ISBN_PESOS]

        self.assertEqual(fila.moneda_origen, "ARS")
        self.assertEqual(fila.valor_origen, 15000.0)
        # 15000 / 970 = 15.4639... -> 15.46, calculado con el valor de venta.
        self.assertEqual(fila.valor_destino, 15.46)

    def test_un_precio_en_dolares_no_se_convierte(self) -> None:
        fila = self._filas("USD")[ISBN_DOLARES]

        self.assertEqual(fila.moneda_origen, "USD")
        self.assertEqual(fila.valor_destino, 29.99)

    def test_no_inventa_valores_para_monedas_sin_cotizacion(self) -> None:
        for fila in self._filas("EUR").values():
            self.assertIsNone(fila.valor_destino)
        for fila in self._filas("JPY").values():
            self.assertIsNone(fila.valor_destino)

    def test_informa_todos_los_libros_del_catalogo(self) -> None:
        self.assertEqual(len(self._filas("USD")), 10)

    def test_multimoneda_deja_vacio_lo_no_convertible(self) -> None:
        filas = self.servicios.libro.listar_precios_multimonetarios(
            self.cotizacion, ["ARS", "USD", "EUR"]
        )
        libro, valores = filas[0]

        self.assertEqual(libro.precio.moneda.codigo, "USD")
        self.assertEqual(valores["ARS"], 29090.3)
        self.assertEqual(valores["USD"], 29.99)
        self.assertIsNone(valores["EUR"])


class PruebaExportacionCsv(unittest.TestCase):
    """Verifica la exportación de precios a un archivo CSV."""

    def setUp(self) -> None:
        self.conexion = apoyo.crear_conexion_migrada()
        self.addCleanup(self.conexion.cerrar)
        self.consola = apoyo.crear_consola(self.conexion)

    def _exportar(self, carpeta: str) -> list:
        with mock.patch.object(
            consola_mod, "CARPETA_EXPORTACION_POR_DEFECTO", carpeta
        ):
            with redirect_stdout(io.StringIO()):
                self.consola._exportar_precios_csv()

        archivos = os.listdir(carpeta)
        self.assertEqual(len(archivos), 1)

        with open(
            os.path.join(carpeta, archivos[0]), encoding="utf-8", newline=""
        ) as archivo:
            return list(csv.DictReader(archivo)), archivos[0]

    def test_genera_un_archivo_con_todas_las_monedas(self) -> None:
        with apoyo.carpeta_temporal("exportacion") as carpeta:
            filas, nombre = self._exportar(carpeta)

        self.assertTrue(nombre.startswith("precios_"))
        self.assertTrue(nombre.endswith(".csv"))
        self.assertEqual(len(filas), 10)

        encabezados = list(filas[0].keys())
        self.assertEqual(
            encabezados[:4],
            ["isbn", "titulo", "moneda_origen", "valor_origen"],
        )
        self.assertEqual(len(encabezados), 4 + 10)

    def test_convierte_pesos_y_dolares(self) -> None:
        with apoyo.carpeta_temporal("exportacion_valores") as carpeta:
            filas, _ = self._exportar(carpeta)

        por_isbn = {fila["isbn"]: fila for fila in filas}
        self.assertEqual(por_isbn[ISBN_PESOS]["valor_origen"], "15000.00")
        self.assertEqual(por_isbn[ISBN_PESOS]["ARS"], "15000.00")
        self.assertEqual(por_isbn[ISBN_PESOS]["USD"], "15.46")
        self.assertEqual(por_isbn[ISBN_DOLARES]["USD"], "29.99")

    def test_las_monedas_sin_cotizacion_quedan_vacias(self) -> None:
        with apoyo.carpeta_temporal("exportacion_vacias") as carpeta:
            filas, _ = self._exportar(carpeta)

        for fila in filas:
            for moneda in ("EUR", "GBP", "BRL", "CLP", "UYU", "MXN", "JPY", "CAD"):
                with self.subTest(moneda=moneda):
                    self.assertEqual(fila[moneda], "")

    def test_crea_la_carpeta_si_no_existe(self) -> None:
        with apoyo.carpeta_temporal("exportacion_nueva") as carpeta:
            destino = os.path.join(carpeta, "subcarpeta")
            with mock.patch.object(
                consola_mod, "CARPETA_EXPORTACION_POR_DEFECTO", destino
            ):
                with redirect_stdout(io.StringIO()):
                    self.consola._exportar_precios_csv()

            self.assertTrue(os.path.isdir(destino))
            self.assertEqual(len(os.listdir(destino)), 1)


if __name__ == "__main__":
    unittest.main()
