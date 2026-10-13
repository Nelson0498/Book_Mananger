"""Pruebas de los modelos ORM: tablas, relaciones y restricciones."""

import unittest
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from book_manager.models.models import (
    Base,
    CotizacionDolarModel,
    EditorialModel,
    GeneroModel,
    LibroModel,
    MonedaModel,
    PrecioModel,
    StockModel,
    TipoCotizacionModel,
)

# Columnas esperadas por tabla. Deben coincidir con los encabezados de los CSV
# de origen, porque la migración es una correspondencia directa entre ambos.
COLUMNAS_ESPERADAS = {
    "generos": ["id", "nombre"],
    "editoriales": ["id", "nombre", "pais"],
    "monedas": ["id", "codigo", "nombre", "simbolo"],
    "tipos_cotizacion": ["id", "nombre"],
    "precios": ["id", "valor", "moneda_id"],
    "libros": [
        "isbn", "titulo", "autor", "editorial_id", "genero_id", "precio_id",
    ],
    "stock": ["id_stock", "libro_isbn", "cantidad", "cantidad_minima"],
    "cotizaciones": [
        "id_cotizacion", "tipo_id", "valor_compra", "valor_venta", "fecha",
    ],
}

CLAVES_FORANEAS_ESPERADAS = {
    ("precios", "moneda_id"): ("monedas", "id"),
    ("libros", "editorial_id"): ("editoriales", "id"),
    ("libros", "genero_id"): ("generos", "id"),
    ("libros", "precio_id"): ("precios", "id"),
    ("stock", "libro_isbn"): ("libros", "isbn"),
    ("cotizaciones", "tipo_id"): ("tipos_cotizacion", "id"),
}


class PruebaEsquema(unittest.TestCase):
    """Verifica la definición declarativa de las tablas."""

    def test_cantidad_de_tablas(self) -> None:
        self.assertEqual(len(Base.metadata.tables), 8)

    def test_columnas_coinciden_con_los_csv(self) -> None:
        for tabla, columnas in COLUMNAS_ESPERADAS.items():
            with self.subTest(tabla=tabla):
                declaradas = [
                    columna.name
                    for columna in Base.metadata.tables[tabla].columns
                ]
                self.assertEqual(declaradas, columnas)

    def test_claves_primarias_sin_autoincremento(self) -> None:
        """Los ids los provee la aplicación: no debe haber secuencias SERIAL."""
        for tabla in Base.metadata.tables.values():
            with self.subTest(tabla=tabla.name):
                ddl = str(
                    CreateTable(tabla).compile(dialect=postgresql.dialect())
                )
                self.assertNotIn("SERIAL", ddl)

    def test_claves_primarias(self) -> None:
        primarias = {
            tabla.name: [columna.name for columna in tabla.primary_key.columns]
            for tabla in Base.metadata.tables.values()
        }
        self.assertEqual(primarias["libros"], ["isbn"])
        self.assertEqual(primarias["stock"], ["id_stock"])
        self.assertEqual(primarias["cotizaciones"], ["id_cotizacion"])
        self.assertEqual(primarias["generos"], ["id"])


class PruebaEsquemaCreado(unittest.TestCase):
    """Verifica el esquema realmente creado en una base de prueba."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.motor = create_engine("sqlite:///:memory:")

        @event.listens_for(cls.motor, "connect")
        def _al_conectar(conexion_dbapi, _registro):
            conexion_dbapi.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(cls.motor)
        cls.inspector = inspect(cls.motor)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.motor.dispose()

    def test_tablas_creadas(self) -> None:
        self.assertEqual(
            sorted(self.inspector.get_table_names()),
            sorted(COLUMNAS_ESPERADAS),
        )

    def test_claves_foraneas(self) -> None:
        for (tabla, columna), (destino, columna_destino) in (
            CLAVES_FORANEAS_ESPERADAS.items()
        ):
            with self.subTest(tabla=tabla, columna=columna):
                foraneas = self.inspector.get_foreign_keys(tabla)
                coincidencias = [
                    fk for fk in foraneas
                    if fk["constrained_columns"] == [columna]
                ]
                self.assertEqual(len(coincidencias), 1, f"Falta FK {tabla}.{columna}")
                self.assertEqual(coincidencias[0]["referred_table"], destino)
                self.assertEqual(
                    coincidencias[0]["referred_columns"], [columna_destino]
                )

    def test_restricciones_de_unicidad(self) -> None:
        esperadas = {
            "generos": [["nombre"]],
            "monedas": [["codigo"]],
            "tipos_cotizacion": [["nombre"]],
            "libros": [["precio_id"]],
            "stock": [["libro_isbn"]],
            "cotizaciones": [["tipo_id", "fecha"]],
        }
        for tabla, restricciones in esperadas.items():
            with self.subTest(tabla=tabla):
                declaradas = [
                    unica["column_names"]
                    for unica in self.inspector.get_unique_constraints(tabla)
                ]
                for restriccion in restricciones:
                    self.assertIn(restriccion, declaradas)

    def test_restricciones_check(self) -> None:
        for tabla, cantidad in (
            ("precios", 1), ("stock", 1), ("cotizaciones", 1)
        ):
            with self.subTest(tabla=tabla):
                self.assertEqual(
                    len(self.inspector.get_check_constraints(tabla)), cantidad
                )


class PruebaRelacionesYRestricciones(unittest.TestCase):
    """Verifica las relaciones entre tablas y la aplicación de restricciones."""

    def setUp(self) -> None:
        self.motor = create_engine("sqlite:///:memory:")

        @event.listens_for(self.motor, "connect")
        def _al_conectar(conexion_dbapi, _registro):
            conexion_dbapi.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(self.motor)

        with Session(self.motor) as sesion:
            sesion.add_all([
                GeneroModel(id=1, nombre="Ficción"),
                EditorialModel(id=1, nombre="Planeta", pais="Argentina"),
                MonedaModel(id=1, codigo="ARS", nombre="Peso", simbolo="$"),
                TipoCotizacionModel(id=1, nombre="Oficial"),
                PrecioModel(id=1, valor=Decimal("15000.00"), moneda_id=1),
                PrecioModel(id=2, valor=Decimal("12500.00"), moneda_id=1),
            ])
            sesion.commit()
            sesion.add(LibroModel(
                isbn="978-950-731-001-1", titulo="Cien años de soledad",
                autor="Gabriel García Márquez", editorial_id=1,
                genero_id=1, precio_id=1,
            ))
            sesion.commit()
            sesion.add(StockModel(
                id_stock=1, libro_isbn="978-950-731-001-1",
                cantidad=25, cantidad_minima=5,
            ))
            sesion.add(CotizacionDolarModel(
                id_cotizacion=1, tipo_id=1, valor_compra=Decimal("900.00"),
                valor_venta=Decimal("950.00"), fecha=date(2024, 1, 15),
            ))
            sesion.commit()

    def tearDown(self) -> None:
        # Se libera el motor para no dejar conexiones SQLite abiertas.
        self.motor.dispose()

    def test_relaciones_bidireccionales(self) -> None:
        with Session(self.motor) as sesion:
            libro = sesion.get(LibroModel, "978-950-731-001-1")
            self.assertEqual(libro.genero.nombre, "Ficción")
            self.assertEqual(libro.editorial.nombre, "Planeta")
            self.assertEqual(libro.precio.moneda.codigo, "ARS")
            self.assertEqual(libro.stock.cantidad, 25)
            self.assertEqual(libro.precio.libro.isbn, libro.isbn)
            self.assertEqual(len(libro.genero.libros), 1)
            self.assertEqual(
                len(sesion.get(TipoCotizacionModel, 1).cotizaciones), 1
            )

    def _probar_restriccion(self, descripcion: str, operacion) -> None:
        with self.subTest(descripcion=descripcion):
            with self.assertRaises(IntegrityError):
                operacion()

    def test_check_precio_no_negativo(self) -> None:
        def operacion():
            with Session(self.motor) as sesion:
                sesion.add(PrecioModel(
                    id=90, valor=Decimal("-1.00"), moneda_id=1
                ))
                sesion.commit()

        self._probar_restriccion("precio negativo", operacion)

    def test_check_compra_no_mayor_que_venta(self) -> None:
        def operacion():
            with Session(self.motor) as sesion:
                sesion.add(CotizacionDolarModel(
                    id_cotizacion=90, tipo_id=1, valor_compra=Decimal("99.00"),
                    valor_venta=Decimal("1.00"), fecha=date(2024, 1, 15),
                ))
                sesion.commit()

        self._probar_restriccion("compra mayor que venta", operacion)

    def test_unicidad_tipo_y_fecha(self) -> None:
        def operacion():
            with Session(self.motor) as sesion:
                sesion.add(CotizacionDolarModel(
                    id_cotizacion=91, tipo_id=1, valor_compra=Decimal("1.00"),
                    valor_venta=Decimal("2.00"), fecha=date(2024, 1, 15),
                ))
                sesion.commit()

        self._probar_restriccion("tipo y fecha repetidos", operacion)

    def test_unicidad_libro_precio_uno_a_uno(self) -> None:
        def operacion():
            with Session(self.motor) as sesion:
                sesion.add(LibroModel(
                    isbn="978-0000-0000-1", titulo="Otro", autor="Autor",
                    editorial_id=1, genero_id=1, precio_id=1,
                ))
                sesion.commit()

        self._probar_restriccion("dos libros con el mismo precio", operacion)

    def test_integridad_referencial(self) -> None:
        def operacion():
            with Session(self.motor) as sesion:
                sesion.add(LibroModel(
                    isbn="978-0000-0000-2", titulo="Otro", autor="Autor",
                    editorial_id=999, genero_id=1, precio_id=2,
                ))
                sesion.commit()

        self._probar_restriccion("editorial inexistente", operacion)

    def test_consulta_de_libros(self) -> None:
        with Session(self.motor) as sesion:
            libros = sesion.execute(select(LibroModel)).scalars().all()
            self.assertEqual(len(libros), 1)


if __name__ == "__main__":
    unittest.main()
