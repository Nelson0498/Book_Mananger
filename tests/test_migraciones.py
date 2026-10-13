"""Pruebas de la migración de datos de CSV a SQL."""

import csv
import inspect
import os
import unittest

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from book_manager.migrations import migrations as mig

from tests import apoyo


class PruebaFirmaDeLaMigracion(unittest.TestCase):
    """Verifica que la función respete la firma pedida por la consigna."""

    def test_firma_de_migrar_datos(self) -> None:
        parametros = list(inspect.signature(mig.migrar_datos).parameters)
        self.assertEqual(parametros, ["carpeta_csvs", "carpeta_sqls"])

    def test_orden_de_tablas_respeta_las_dependencias(self) -> None:
        tablas = [definicion.tabla for definicion in mig.DEFINICIONES_TABLAS]
        self.assertEqual(tablas, [
            "generos", "editoriales", "monedas", "tipos_cotizacion",
            "precios", "libros", "stock", "cotizaciones",
        ])
        # Cada tabla debe aparecer después de aquellas a las que referencia.
        self.assertLess(tablas.index("monedas"), tablas.index("precios"))
        self.assertLess(tablas.index("precios"), tablas.index("libros"))
        self.assertLess(tablas.index("libros"), tablas.index("stock"))
        self.assertLess(
            tablas.index("tipos_cotizacion"), tablas.index("cotizaciones")
        )


class PruebaGeneracionDeScripts(unittest.TestCase):
    """Verifica los archivos .sql generados a partir de los CSV."""

    def test_genera_un_script_por_tabla_en_orden(self) -> None:
        with apoyo.carpeta_temporal("sql") as carpeta:
            rutas = mig.migrar_datos(mig.CARPETA_CSV_POR_DEFECTO, carpeta)

            self.assertEqual(len(rutas), 8)
            nombres = [os.path.basename(ruta) for ruta in rutas]
            self.assertEqual(nombres, [
                "01_generos.sql", "02_editoriales.sql", "03_monedas.sql",
                "04_tipos_cotizacion.sql", "05_precios.sql", "06_libros.sql",
                "07_stock.sql", "08_cotizaciones.sql",
            ])
            for ruta in rutas:
                self.assertTrue(os.path.exists(ruta))

    def test_los_scripts_son_idempotentes(self) -> None:
        with apoyo.carpeta_temporal("sql_idempotente") as carpeta:
            rutas = mig.migrar_datos(mig.CARPETA_CSV_POR_DEFECTO, carpeta)

            for ruta in rutas:
                with open(ruta, encoding="utf-8") as archivo:
                    contenido = archivo.read()
                self.assertIn("INSERT INTO", contenido)
                self.assertIn("ON CONFLICT DO NOTHING;", contenido)

    def test_conserva_los_acentos(self) -> None:
        with apoyo.carpeta_temporal("sql_acentos") as carpeta:
            rutas = mig.migrar_datos(mig.CARPETA_CSV_POR_DEFECTO, carpeta)

            with open(rutas[0], encoding="utf-8") as archivo:
                contenido = archivo.read()
            self.assertIn("Ficción", contenido)

    def test_falla_si_no_encuentra_un_csv(self) -> None:
        with apoyo.carpeta_temporal("sql_sin_csv") as carpeta:
            with self.assertRaises(FileNotFoundError):
                mig.migrar_datos(carpeta, carpeta)

    def test_falla_si_las_columnas_no_coinciden(self) -> None:
        with apoyo.carpeta_temporal("sql_columnas") as origen:
            with apoyo.carpeta_temporal("sql_columnas_salida") as destino:
                for definicion in mig.DEFINICIONES_TABLAS:
                    ruta = os.path.join(origen, definicion.archivo_csv)
                    with open(ruta, "w", encoding="utf-8", newline="") as archivo:
                        archivo.write("columna_inesperada\n1\n")

                with self.assertRaises(ValueError):
                    mig.migrar_datos(origen, destino)


class PruebaAplicacionDeLaMigracion(unittest.TestCase):
    """Verifica la aplicación de los scripts sobre una base de prueba."""

    def setUp(self) -> None:
        self.conexion = apoyo.crear_conexion_vacia()

    def tearDown(self) -> None:
        self.conexion.cerrar()

    def _contar(self, tabla: str) -> int:
        with self.conexion.obtener_sesion() as sesion:
            return sesion.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar()

    def test_migra_todos_los_registros(self) -> None:
        with apoyo.carpeta_temporal("migracion_datos") as carpeta:
            resultado = mig.migrar_base_de_datos(
                self.conexion, carpeta_sqls=carpeta
            )

        self.assertEqual(len(resultado), 8)
        for definicion in mig.DEFINICIONES_TABLAS:
            with self.subTest(tabla=definicion.tabla):
                with open(
                    os.path.join(
                        mig.CARPETA_CSV_POR_DEFECTO, definicion.archivo_csv
                    ),
                    encoding="utf-8",
                ) as archivo:
                    esperados = len(list(csv.DictReader(archivo)))

                self.assertEqual(self._contar(definicion.tabla), esperados)
                self.assertEqual(esperados, 10)

    def test_es_idempotente(self) -> None:
        with apoyo.carpeta_temporal("migracion_idempotente") as carpeta:
            mig.migrar_base_de_datos(self.conexion, carpeta_sqls=carpeta)
            segunda = mig.migrar_base_de_datos(
                self.conexion, carpeta_sqls=carpeta
            )

        self.assertEqual(sum(segunda.values()), 0)
        self.assertEqual(self._contar("libros"), 10)
        self.assertEqual(self._contar("cotizaciones"), 10)

    def test_no_confirma_nada_si_un_script_falla(self) -> None:
        with apoyo.carpeta_temporal("migracion_fallida") as carpeta:
            with open(
                os.path.join(carpeta, "01_bueno.sql"), "w", encoding="utf-8"
            ) as archivo:
                archivo.write(
                    "INSERT INTO generos (id, nombre) VALUES (1, 'X')"
                    " ON CONFLICT DO NOTHING;\n"
                )
            with open(
                os.path.join(carpeta, "02_malo.sql"), "w", encoding="utf-8"
            ) as archivo:
                archivo.write("INSERT INTO tabla_inexistente (id) VALUES (1);\n")

            with self.assertRaises(OperationalError):
                mig.aplicar_migracion(self.conexion, carpeta)

        self.assertEqual(self._contar("generos"), 0)

    def test_falla_si_no_hay_scripts(self) -> None:
        with apoyo.carpeta_temporal("migracion_vacia") as carpeta:
            with self.assertRaises(FileNotFoundError):
                mig.aplicar_migracion(self.conexion, carpeta)

    def test_crear_tablas_es_idempotente(self) -> None:
        mig.crear_tablas(self.conexion)
        mig.crear_tablas(self.conexion)
        self.assertEqual(self._contar("generos"), 0)


class PruebaSeparacionDeEstructuraYDatos(unittest.TestCase):
    """La migración de datos no debe tocar los scripts de estructura."""

    def test_las_carpetas_por_defecto_estan_separadas(self) -> None:
        self.assertNotEqual(
            mig.CARPETA_SQL_ESTRUCTURA_POR_DEFECTO,
            mig.CARPETA_SQL_DATOS_POR_DEFECTO,
        )
        self.assertTrue(
            mig.CARPETA_SQL_ESTRUCTURA_POR_DEFECTO.endswith(
                os.path.join("migrations", "sql")
            )
        )
        self.assertTrue(
            mig.CARPETA_SQL_DATOS_POR_DEFECTO.endswith(
                os.path.join("migrations", "sql_datos_generados")
            )
        )

    def test_generar_datos_no_sobrescribe_los_scripts_de_estructura(self) -> None:
        guion = "CREATE TABLE ejemplo (id INTEGER);\n"

        with apoyo.carpeta_temporal("separacion_estructura") as estructura:
            with apoyo.carpeta_temporal("separacion_datos") as datos:
                ruta_estructura = os.path.join(estructura, "01_tablas.sql")
                with open(ruta_estructura, "w", encoding="utf-8") as archivo:
                    archivo.write(guion)

                mig.migrar_datos(mig.CARPETA_CSV_POR_DEFECTO, datos)

                with open(ruta_estructura, encoding="utf-8") as archivo:
                    self.assertEqual(archivo.read(), guion)
                self.assertEqual(os.listdir(estructura), ["01_tablas.sql"])
                self.assertEqual(len(os.listdir(datos)), 8)

    def test_aplicar_migracion_rechaza_sentencias_de_estructura(self) -> None:
        conexion = apoyo.crear_conexion_vacia()
        self.addCleanup(conexion.cerrar)

        with apoyo.carpeta_temporal("migracion_con_ddl") as carpeta:
            with open(
                os.path.join(carpeta, "01_estructura.sql"), "w",
                encoding="utf-8",
            ) as archivo:
                archivo.write("CREATE TABLE inventada (id INTEGER);\n")

            with self.assertRaises(ValueError) as contexto:
                mig.aplicar_migracion(conexion, carpeta)

        self.assertIn("estructura", str(contexto.exception))

    def test_aplicar_migracion_solo_ejecuta_los_scripts_de_datos(self) -> None:
        conexion = apoyo.crear_conexion_vacia()
        self.addCleanup(conexion.cerrar)

        with apoyo.carpeta_temporal("solo_datos_estructura") as estructura:
            with apoyo.carpeta_temporal("solo_datos_datos") as datos:
                with open(
                    os.path.join(estructura, "01_estructura.sql"), "w",
                    encoding="utf-8",
                ) as archivo:
                    archivo.write("CREATE TABLE inventada (id INTEGER);\n")
                with open(
                    os.path.join(datos, "01_datos.sql"), "w", encoding="utf-8"
                ) as archivo:
                    archivo.write(
                        "INSERT INTO generos (id, nombre) VALUES (99, 'X')"
                        " ON CONFLICT DO NOTHING;\n"
                    )

                resultado = mig.aplicar_migracion(conexion, datos)

                self.assertEqual(list(resultado), ["01_datos.sql"])
                with conexion.obtener_sesion() as sesion:
                    self.assertEqual(
                        sesion.execute(
                            text("SELECT COUNT(*) FROM generos")
                        ).scalar(),
                        1,
                    )


class PruebaCodificacionDeArchivos(unittest.TestCase):
    """Lectura de CSV y escritura de SQL con acentos y ñ."""

    CONTENIDOS = {
        "generos.csv": "id,nombre\n1,Ficción\n2,Poesía\n",
        "editoriales.csv": "id,nombre,pais\n1,Emecé,España\n",
        "monedas.csv": "id,codigo,nombre,simbolo\n1,ARS,Peso Argentino,$\n",
        "tipos_cotizacion.csv": "id,nombre\n1,Oficial\n",
        "precios.csv": "id,valor,moneda_id\n1,1500.0,1\n",
        "libros.csv": (
            "isbn,titulo,autor,editorial_id,genero_id,precio_id\n"
            "978-1,Cien años de soledad,Gabriel García Márquez,1,1,1\n"
        ),
        "stock.csv": (
            "libro_isbn,id_stock,cantidad,cantidad_minima\n978-1,1,5,1\n"
        ),
        "cotizaciones.csv": (
            "id_cotizacion,tipo_id,valor_compra,valor_venta,fecha\n"
            "1,1,900.0,950.0,2024-01-15\n"
        ),
    }

    def _escribir_csvs(self, carpeta: str, codificacion: str) -> None:
        """Escribe un juego completo de CSV con el texto acentuado."""
        for nombre, texto in self.CONTENIDOS.items():
            with open(
                os.path.join(carpeta, nombre), "w",
                encoding=codificacion, newline="",
            ) as archivo:
                archivo.write(texto)

    def _leer(self, ruta: str) -> str:
        with open(ruta, encoding="utf-8") as archivo:
            return archivo.read()

    def test_lee_acentos_y_ene(self) -> None:
        with apoyo.carpeta_temporal("codificacion_utf8") as origen:
            with apoyo.carpeta_temporal("codificacion_utf8_sql") as destino:
                self._escribir_csvs(origen, "utf-8")
                rutas = mig.migrar_datos(origen, destino)

                generos = self._leer(rutas[0])
                self.assertIn("'Ficción'", generos)
                self.assertIn("'Poesía'", generos)

                editoriales = self._leer(rutas[1])
                self.assertIn("'Emecé'", editoriales)
                self.assertIn("'España'", editoriales)

                libros = self._leer(rutas[5])
                self.assertIn("Cien años de soledad", libros)
                self.assertIn("Gabriel García Márquez", libros)

    def test_lee_un_csv_guardado_con_bom(self) -> None:
        with apoyo.carpeta_temporal("codificacion_bom") as origen:
            with apoyo.carpeta_temporal("codificacion_bom_sql") as destino:
                self._escribir_csvs(origen, "utf-8-sig")
                rutas = mig.migrar_datos(origen, destino)

                generos = self._leer(rutas[0])

        # Sin el BOM en el encabezado: la primera columna se llama "id".
        self.assertIn("INSERT INTO generos (id, nombre)", generos)
        self.assertIn("'Ficción'", generos)
        self.assertNotIn("\ufeff", generos)

    def test_los_scripts_generados_estan_en_utf8_sin_bom(self) -> None:
        with apoyo.carpeta_temporal("codificacion_salida") as carpeta:
            rutas = mig.migrar_datos(mig.CARPETA_CSV_POR_DEFECTO, carpeta)

            with open(rutas[0], "rb") as archivo:
                crudo = archivo.read()

        self.assertFalse(crudo.startswith(b"\xef\xbb\xbf"))
        self.assertIn("Ficción".encode("utf-8"), crudo)
        self.assertNotIn("Ficción".encode("latin-1"), crudo)


if __name__ == "__main__":
    unittest.main()
