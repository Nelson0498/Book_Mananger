"""Pruebas de la integración con la API de cotizaciones del dólar.

Ninguna prueba accede a la red: la descarga se reemplaza por datos simulados,
de modo que los resultados son deterministas y no dependen de la disponibilidad
del servicio externo.
"""

import datetime
import os
import unittest
import urllib.error
from unittest import mock

from book_manager.services import services as svc_mod
from book_manager.services.services import (
    EntidadNoEncontradaError,
    ErrorServicio,
    OperacionInvalidaError,
    _fecha_desde_api,
)

from tests import apoyo

URL_FALSA = "https://api.test/dolares"

# Respuesta representativa de la API, con las siete casas que publica.
RESPUESTA_API = [
    {
        "moneda": "USD", "casa": "oficial", "nombre": "Oficial",
        "compra": 1485, "venta": 1535,
        "fechaActualizacion": "2026-10-13T14:00:00.000Z",
    },
    {
        "moneda": "USD", "casa": "blue", "nombre": "Blue",
        "compra": 1530, "venta": 1550,
        "fechaActualizacion": "2026-10-13T16:57:00.000Z",
    },
    {
        "moneda": "USD", "casa": "bolsa", "nombre": "Bolsa",
        "compra": 1537.5, "venta": 1538.4,
        "fechaActualizacion": "2026-10-13T16:57:00.000Z",
    },
    {
        "moneda": "USD", "casa": "contadoconliqui",
        "nombre": "Contado con liquidación",
        "compra": 1611.9, "venta": 1612.4,
        "fechaActualizacion": "2026-10-13T16:57:00.000Z",
    },
    {
        "moneda": "USD", "casa": "mayorista", "nombre": "Mayorista",
        "compra": 1506, "venta": 1515,
        "fechaActualizacion": "2026-10-13T13:50:00.000Z",
    },
    {
        "moneda": "USD", "casa": "cripto", "nombre": "Cripto",
        "compra": 1608.25, "venta": 1611.18,
        "fechaActualizacion": "2026-10-13T16:57:00.000Z",
    },
    {
        "moneda": "USD", "casa": "tarjeta", "nombre": "Tarjeta",
        "compra": 1930.5, "venta": 1995.5,
        "fechaActualizacion": "2026-10-13T14:00:00.000Z",
    },
]

FECHA_API = datetime.date(2026, 10, 13)


class _RespuestaFalsa:
    """Respuesta HTTP mínima para probar la descarga sin salir a la red."""

    def __init__(self, contenido: bytes) -> None:
        self._contenido = contenido

    def read(self) -> bytes:
        return self._contenido

    def __enter__(self) -> "_RespuestaFalsa":
        return self

    def __exit__(self, *_argumentos) -> bool:
        return False


class PruebaDescargaDeLaApi(unittest.TestCase):
    """Verifica la descarga HTTP propiamente dicha, sin salir a la red."""

    def test_devuelve_la_lista_cuando_la_respuesta_es_valida(self) -> None:
        with mock.patch.object(
            svc_mod.urllib.request, "urlopen",
            return_value=_RespuestaFalsa(b'[{"casa": "oficial"}]'),
        ):
            datos = svc_mod._descargar_cotizaciones(URL_FALSA)

        self.assertEqual(datos, [{"casa": "oficial"}])

    def test_envia_user_agent_y_tiempo_de_espera(self) -> None:
        capturado = {}

        def urlopen_falso(peticion, timeout=None):
            capturado["peticion"] = peticion
            capturado["timeout"] = timeout
            return _RespuestaFalsa(b"[]")

        with mock.patch.object(
            svc_mod.urllib.request, "urlopen", side_effect=urlopen_falso
        ):
            svc_mod._descargar_cotizaciones(URL_FALSA)

        encabezados = {
            clave.lower(): valor
            for clave, valor in capturado["peticion"].header_items()
        }
        self.assertEqual(encabezados["user-agent"], svc_mod.USER_AGENT_API)
        self.assertEqual(capturado["timeout"], svc_mod.ESPERA_API_SEGUNDOS)
        self.assertEqual(capturado["peticion"].full_url, URL_FALSA)


class PruebaFechaDeLaApi(unittest.TestCase):
    """Verifica la interpretación del campo `fechaActualizacion`."""

    def test_convierte_la_marca_de_tiempo(self) -> None:
        self.assertEqual(
            _fecha_desde_api("2026-10-13T14:00:00.000Z"), FECHA_API
        )

    def test_usa_la_fecha_actual_si_no_se_informa(self) -> None:
        self.assertEqual(_fecha_desde_api(None), datetime.date.today())


class PruebaObtenerCotizaciones(unittest.TestCase):
    """Verifica la descarga, el mapeo y el registro de cotizaciones."""

    def setUp(self) -> None:
        self.conexion = apoyo.crear_conexion_migrada()
        self.servicios = apoyo.crear_servicios(self.conexion)
        self.entorno = mock.patch.dict(os.environ, {"API_URL": URL_FALSA})
        self.entorno.start()
        self.addCleanup(self.entorno.stop)
        self.addCleanup(self.conexion.cerrar)

    def _obtener(self, respuesta: list) -> list:
        with mock.patch.object(
            svc_mod, "_descargar_cotizaciones", return_value=respuesta
        ):
            return self.servicios.cotizacion.obtener_cotizaciones()

    def _total_cotizaciones(self) -> int:
        """Cuenta los registros de cotizaciones existentes en la base."""
        return len(
            apoyo.crear_repositorios(self.conexion).cotizacion.leer_todos()
        )

    def test_registra_las_siete_casas(self) -> None:
        obtenidas = self._obtener(RESPUESTA_API)

        self.assertEqual(len(obtenidas), 7)
        self.assertEqual(
            len(self.servicios.cotizacion.historico(1)), 3
        )

    def test_mapea_las_casas_con_nombres_no_literales(self) -> None:
        """`bolsa` corresponde al MEP y `contadoconliqui` al CCL."""
        obtenidas = self._obtener(RESPUESTA_API)
        nombres = {c.tipo.nombre: c for c in obtenidas}

        self.assertIn("MEP", nombres)
        self.assertIn("CCL", nombres)
        self.assertEqual(nombres["MEP"].valor_venta, 1538.4)
        self.assertEqual(nombres["CCL"].valor_compra, 1611.9)

    def test_usa_la_fecha_informada_por_la_api(self) -> None:
        obtenidas = self._obtener(RESPUESTA_API)

        for cotizacion in obtenidas:
            self.assertEqual(cotizacion.fecha, FECHA_API)

    def test_no_duplica_si_se_repite_la_consulta(self) -> None:
        self._obtener(RESPUESTA_API)
        antes = self._total_cotizaciones()

        actualizada = [
            dict(registro, compra=1000, venta=2000)
            for registro in RESPUESTA_API
        ]
        self._obtener(actualizada)
        despues = self._total_cotizaciones()

        self.assertEqual(antes, despues)
        self.assertEqual(
            self.servicios.cotizacion.obtener_vigente(1).valor_venta, 2000.0
        )

    def test_ignora_las_casas_desconocidas(self) -> None:
        respuesta = [
            RESPUESTA_API[0],
            {
                "casa": "casa_nueva", "compra": 1, "venta": 2,
                "fechaActualizacion": "2026-10-13T14:00:00.000Z",
            },
        ]

        self.assertEqual(len(self._obtener(respuesta)), 1)

    def test_ignora_los_registros_sin_valores(self) -> None:
        respuesta = [
            {
                "casa": "oficial", "compra": None, "venta": None,
                "fechaActualizacion": "2026-10-13T14:00:00.000Z",
            },
            RESPUESTA_API[1],
        ]

        obtenidas = self._obtener(respuesta)

        self.assertEqual(len(obtenidas), 1)
        self.assertEqual(obtenidas[0].tipo.nombre, "Blue")

    def test_falla_si_no_hay_api_url(self) -> None:
        with mock.patch.dict(os.environ, {"API_URL": ""}):
            with self.assertRaises(OperacionInvalidaError):
                self.servicios.cotizacion.obtener_cotizaciones()

    def test_falla_si_la_api_no_responde(self) -> None:
        with mock.patch.object(
            svc_mod, "_descargar_cotizaciones",
            side_effect=urllib.error.URLError("sin conexión"),
        ):
            with self.assertRaises(ErrorServicio):
                self.servicios.cotizacion.obtener_cotizaciones()

    def test_ignora_los_registros_que_no_son_objetos(self) -> None:
        respuesta = ["texto suelto", RESPUESTA_API[0]]

        self.assertEqual(len(self._obtener(respuesta)), 1)

    def test_falla_si_la_respuesta_no_es_una_lista(self) -> None:
        """La validación vive en la descarga, que aquí no está simulada."""
        with mock.patch.object(
            svc_mod.urllib.request, "urlopen",
            return_value=_RespuestaFalsa(b'{"no": "es una lista"}'),
        ):
            with self.assertRaises(ValueError):
                svc_mod._descargar_cotizaciones(URL_FALSA)

    def test_falla_si_no_hay_cotizaciones_reconocidas(self) -> None:
        with self.assertRaises(ErrorServicio):
            self._obtener([])

    def test_falla_si_falta_el_tipo_y_no_escribe_nada(self) -> None:
        conexion_vacia = apoyo.crear_conexion_vacia()
        self.addCleanup(conexion_vacia.cerrar)
        servicios_vacios = apoyo.crear_servicios(conexion_vacia)

        with mock.patch.object(
            svc_mod, "_descargar_cotizaciones", return_value=RESPUESTA_API
        ):
            with self.assertRaises(EntidadNoEncontradaError):
                servicios_vacios.cotizacion.obtener_cotizaciones()

        self.assertEqual(
            len(apoyo.crear_repositorios(conexion_vacia).cotizacion.leer_todos()),
            0,
        )


if __name__ == "__main__":
    unittest.main()
