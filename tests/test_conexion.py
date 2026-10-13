"""Pruebas de la conexión, las sesiones y las transacciones."""

import os
import unittest
from unittest import mock

from book_manager.database.connection import ConexionDB, normalizar_url
from book_manager.models.models import GeneroModel

from tests import apoyo


class PruebaNormalizarUrl(unittest.TestCase):
    """Verifica la normalización de la URL de conexión."""

    def test_agrega_el_driver_psycopg(self) -> None:
        url = "postgresql://usuario:clave@host:5432/base"
        self.assertEqual(
            normalizar_url(url),
            "postgresql+psycopg://usuario:clave@host:5432/base",
        )

    def test_respeta_una_url_con_driver_explicito(self) -> None:
        url = "postgresql+psycopg://usuario:clave@host:5432/base"
        self.assertEqual(normalizar_url(url), url)

    def test_no_modifica_otras_urls(self) -> None:
        url = "sqlite:///:memory:"
        self.assertEqual(normalizar_url(url), url)


class PruebaConexionDB(unittest.TestCase):
    """Verifica la creación del motor de SQLAlchemy."""

    def test_falla_si_no_hay_url_configurada(self) -> None:
        with mock.patch.dict(os.environ, {"DATABASE_URL": ""}):
            with self.assertRaises(ValueError):
                ConexionDB()

    def test_probar_conexion(self) -> None:
        conexion = ConexionDB(database_url="sqlite:///:memory:")
        try:
            self.assertTrue(conexion.probar_conexion())
        finally:
            conexion.cerrar()


class PruebaSesionesYTransacciones(unittest.TestCase):
    """Verifica el contrato de `obtener_sesion` y de `transaccion`."""

    def setUp(self) -> None:
        self.conexion = apoyo.crear_conexion_migrada()

    def tearDown(self) -> None:
        self.conexion.cerrar()

    def test_transaccion_confirma_los_cambios(self) -> None:
        with self.conexion.transaccion() as sesion:
            sesion.add(GeneroModel(id=99, nombre="Ensayo"))

        with self.conexion.obtener_sesion() as sesion:
            self.assertIsNotNone(sesion.get(GeneroModel, 99))

    def test_transaccion_revierte_ante_un_error(self) -> None:
        with self.assertRaises(RuntimeError):
            with self.conexion.transaccion() as sesion:
                sesion.add(GeneroModel(id=98, nombre="Ensayo"))
                raise RuntimeError("fallo simulado")

        with self.conexion.obtener_sesion() as sesion:
            self.assertIsNone(sesion.get(GeneroModel, 98))

    def test_obtener_sesion_no_confirma_los_cambios(self) -> None:
        with self.conexion.obtener_sesion() as sesion:
            sesion.add(GeneroModel(id=97, nombre="Ensayo"))
            sesion.flush()

        with self.conexion.obtener_sesion() as sesion:
            self.assertIsNone(sesion.get(GeneroModel, 97))


if __name__ == "__main__":
    unittest.main()
