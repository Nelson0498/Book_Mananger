"""
Carga de datos iniciales para el sistema Book Manager – Sprint 1.

Genera un mínimo de 10 registros por entidad con relaciones
consistentes entre sí.  Los datos se escriben directamente en
los repositorios; si un repositorio ya tiene datos, se omite
la carga de esa entidad para evitar duplicados.
"""

import datetime

from book_manager.entities.entities import (
    CotizacionDolar,
    Editorial,
    Genero,
    Moneda,
    Precio,
    Stock,
    TipoCotizacion,
)
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar,
    RepositorioEditorial,
    RepositorioGenero,
    RepositorioLibro,
    RepositorioMoneda,
    RepositorioPrecio,
    RepositorioStock,
    RepositorioTipoCotizacion,
)


def cargar_datos_iniciales(
    repositorio_genero: RepositorioGenero,
    repositorio_editorial: RepositorioEditorial,
    repositorio_moneda: RepositorioMoneda,
    repositorio_tipo_cotizacion: RepositorioTipoCotizacion,
    repositorio_precio: RepositorioPrecio,
    repositorio_stock: RepositorioStock,
    repositorio_libro: RepositorioLibro,
    repositorio_cotizacion: RepositorioCotizacionDolar,
) -> None:
    """Carga datos iniciales si los repositorios están vacíos."""

    # ------------------------------------------------------------------
    # Géneros (10)
    # ------------------------------------------------------------------
    if not repositorio_genero.leer_todos():
        generos = [
            Genero(id_genero=1, nombre="Ficción"),
            Genero(id_genero=2, nombre="No Ficción"),
            Genero(id_genero=3, nombre="Ciencia Ficción"),
            Genero(id_genero=4, nombre="Terror"),
            Genero(id_genero=5, nombre="Romance"),
            Genero(id_genero=6, nombre="Fantasía"),
            Genero(id_genero=7, nombre="Historia"),
            Genero(id_genero=8, nombre="Biografía"),
            Genero(id_genero=9, nombre="Poesía"),
            Genero(id_genero=10, nombre="Aventura"),
        ]
        for g in generos:
            repositorio_genero.crear(g)
        print("  [OK] Géneros precargados (10)")

    # ------------------------------------------------------------------
    # Editoriales (10)
    # ------------------------------------------------------------------
    if not repositorio_editorial.leer_todos():
        editoriales = [
            Editorial(id_editorial=1, nombre="Planeta",
                      pais="Argentina"),
            Editorial(id_editorial=2, nombre="Penguin Random House",
                      pais="España"),
            Editorial(id_editorial=3, nombre="Alfaguara",
                      pais="España"),
            Editorial(id_editorial=4, nombre="Emecé",
                      pais="Argentina"),
            Editorial(id_editorial=5, nombre="Sudamericana",
                      pais="Argentina"),
            Editorial(id_editorial=6, nombre="Anagrama",
                      pais="España"),
            Editorial(id_editorial=7, nombre="Tusquets",
                      pais="España"),
            Editorial(id_editorial=8, nombre="Siglo XXI",
                      pais="México"),
            Editorial(id_editorial=9, nombre="Fondo de Cultura Económica",
                      pais="México"),
            Editorial(id_editorial=10, nombre="Salamandra",
                      pais="España"),
        ]
        for e in editoriales:
            repositorio_editorial.crear(e)
        print("  [OK] Editoriales precargadas (10)")

    # ------------------------------------------------------------------
    # Monedas (10)
    # ------------------------------------------------------------------
    if not repositorio_moneda.leer_todos():
        monedas = [
            Moneda(id_moneda=1, codigo="ARS",
                   nombre="Peso Argentino", simbolo="$"),
            Moneda(id_moneda=2, codigo="USD",
                   nombre="Dólar Estadounidense", simbolo="US$"),
            Moneda(id_moneda=3, codigo="EUR",
                   nombre="Euro", simbolo="€"),
            Moneda(id_moneda=4, codigo="GBP",
                   nombre="Libra Esterlina", simbolo="£"),
            Moneda(id_moneda=5, codigo="BRL",
                   nombre="Real Brasileño", simbolo="R$"),
            Moneda(id_moneda=6, codigo="CLP",
                   nombre="Peso Chileno", simbolo="CL$"),
            Moneda(id_moneda=7, codigo="UYU",
                   nombre="Peso Uruguayo", simbolo="$U"),
            Moneda(id_moneda=8, codigo="MXN",
                   nombre="Peso Mexicano", simbolo="MX$"),
            Moneda(id_moneda=9, codigo="JPY",
                   nombre="Yen Japonés", simbolo="¥"),
            Moneda(id_moneda=10, codigo="CAD",
                   nombre="Dólar Canadiense", simbolo="C$"),
        ]
        for m in monedas:
            repositorio_moneda.crear(m)
        print("  [OK] Monedas precargadas (10)")

    # ------------------------------------------------------------------
    # Tipos de cotización (10)
    # ------------------------------------------------------------------
    if not repositorio_tipo_cotizacion.leer_todos():
        tipos = [
            TipoCotizacion(id_tipo=1, nombre="Oficial"),
            TipoCotizacion(id_tipo=2, nombre="Blue"),
            TipoCotizacion(id_tipo=3, nombre="MEP"),
            TipoCotizacion(id_tipo=4, nombre="CCL"),
            TipoCotizacion(id_tipo=5, nombre="Tarjeta"),
            TipoCotizacion(id_tipo=6, nombre="Mayorista"),
            TipoCotizacion(id_tipo=7, nombre="Cripto"),
            TipoCotizacion(id_tipo=8, nombre="Turista"),
            TipoCotizacion(id_tipo=9, nombre="Solidario"),
            TipoCotizacion(id_tipo=10, nombre="Libre"),
        ]
        for t in tipos:
            repositorio_tipo_cotizacion.crear(t)
        print("  [OK] Tipos de cotización precargados (10)")

    # ------------------------------------------------------------------
    # Precios (10)  –  cada uno apunta a una moneda existente
    # Se usan ids 1-10 ; monedas 1 (ARS) y 2 (USD) alternadas.
    # ------------------------------------------------------------------
    if not repositorio_precio.leer_todos():
        precios_data = [
            (1, 15000.00, 1),   # ARS
            (2, 12500.00, 1),   # ARS
            (3, 29.99, 2),      # USD
            (4, 18900.00, 1),   # ARS
            (5, 35.50, 2),      # USD
            (6, 9800.00, 1),    # ARS
            (7, 22.00, 2),      # USD
            (8, 14200.00, 1),   # ARS
            (9, 19.99, 2),      # USD
            (10, 11500.00, 1),  # ARS
        ]
        for id_p, valor, moneda_id in precios_data:
            moneda = repositorio_moneda.leer_por_id(moneda_id)
            if moneda is None:
                raise ValueError(
                    f"Moneda con id {moneda_id} no encontrada "
                    f"durante precarga de precios"
                )
            repositorio_precio.crear(
                Precio(id_precio=id_p, valor=valor, moneda=moneda)
            )
        print("  [OK] Precios precargados (10)")

    # ------------------------------------------------------------------
    # Libros (10)  –  relaciones: editorial, genero, precio existentes
    # ------------------------------------------------------------------
    # isbn → (titulo, autor, editorial_id, genero_id, precio_id)
    libros_data = [
        ("978-950-731-001-1",
         "Cien años de soledad",
         "Gabriel García Márquez", 1, 1, 1),
        ("978-950-731-002-8",
         "El túnel",
         "Ernesto Sabato", 4, 1, 2),
        ("978-84-204-8311-5",
         "Fahrenheit 451",
         "Ray Bradbury", 2, 3, 3),
        ("978-987-566-847-3",
         "El Aleph",
         "Jorge Luis Borges", 5, 6, 4),
        ("978-84-339-7082-9",
         "1984",
         "George Orwell", 6, 3, 5),
        ("978-950-49-0001-2",
         "Martín Fierro",
         "José Hernández", 3, 9, 6),
        ("978-84-7223-084-0",
         "Drácula",
         "Bram Stoker", 10, 4, 7),
        ("978-987-1210-01-6",
         "Historia económica de la Argentina",
         "Aldo Ferrer", 9, 7, 8),
        ("978-84-9838-133-5",
         "Orgullo y prejuicio",
         "Jane Austen", 7, 5, 9),
        ("978-987-04-0156-3",
         "Rayuela",
         "Julio Cortázar", 5, 1, 10),
    ]

    if not repositorio_libro.leer_todos():
        from book_manager.entities.entities import Libro
        for isbn, titulo, autor, ed_id, gen_id, pre_id in libros_data:
            genero = repositorio_genero.leer_por_id(gen_id)
            editorial = repositorio_editorial.leer_por_id(ed_id)
            precio = repositorio_precio.leer_por_id(pre_id)
            if genero is None or editorial is None or precio is None:
                raise ValueError(
                    f"Datos relacionados no encontrados para libro {isbn}"
                )
            stock_placeholder = Stock(
                id_stock=0, cantidad=0, libro_isbn=isbn
            )
            libro = Libro(
                isbn=isbn, titulo=titulo, autor=autor,
                editorial=editorial, genero=genero,
                precio=precio, stock=stock_placeholder,
            )
            repositorio_libro.crear(libro)
        print("  [OK] Libros precargados (10)")

    # ------------------------------------------------------------------
    # Stock (10)  –  un stock por cada libro, con isbn correspondiente
    # ------------------------------------------------------------------
    if not repositorio_stock.leer_todos():
        stocks_data = [
            (1, "978-950-731-001-1", 25, 5),
            (2, "978-950-731-002-8", 18, 3),
            (3, "978-84-204-8311-5", 12, 2),
            (4, "978-987-566-847-3", 30, 5),
            (5, "978-84-339-7082-9", 8, 3),
            (6, "978-950-49-0001-2", 40, 10),
            (7, "978-84-7223-084-0", 15, 4),
            (8, "978-987-1210-01-6", 6, 2),
            (9, "978-84-9838-133-5", 22, 5),
            (10, "978-987-04-0156-3", 35, 8),
        ]
        for id_s, isbn, cant, cant_min in stocks_data:
            repositorio_stock.crear(
                Stock(
                    id_stock=id_s, cantidad=cant,
                    cantidad_minima=cant_min, libro_isbn=isbn,
                )
            )
        print("  [OK] Stocks precargados (10)")

    # ------------------------------------------------------------------
    # Cotizaciones del dólar (10)
    # Distribuidas entre varios tipos y fechas distintas.
    # ------------------------------------------------------------------
    if not repositorio_cotizacion.leer_todos():
        cotizaciones_data = [
            # (id, tipo_id, compra, venta, fecha)
            (1, 1, 900.00, 950.00,
             datetime.date(2024, 1, 15)),
            (2, 1, 920.00, 970.00,
             datetime.date(2024, 2, 15)),
            (3, 2, 1100.00, 1150.00,
             datetime.date(2024, 1, 15)),
            (4, 2, 1120.00, 1180.00,
             datetime.date(2024, 2, 15)),
            (5, 3, 1050.00, 1080.00,
             datetime.date(2024, 1, 15)),
            (6, 3, 1070.00, 1100.00,
             datetime.date(2024, 2, 15)),
            (7, 4, 1060.00, 1090.00,
             datetime.date(2024, 1, 15)),
            (8, 5, 1300.00, 1350.00,
             datetime.date(2024, 1, 15)),
            (9, 6, 890.00, 910.00,
             datetime.date(2024, 1, 15)),
            (10, 7, 1200.00, 1250.00,
             datetime.date(2024, 1, 15)),
        ]
        for id_c, tipo_id, compra, venta, fecha in cotizaciones_data:
            tipo = repositorio_tipo_cotizacion.leer_por_id(tipo_id)
            if tipo is None:
                raise ValueError(
                    f"Tipo de cotización con id {tipo_id} "
                    f"no encontrado durante precarga"
                )
            repositorio_cotizacion.crear(
                CotizacionDolar(
                    id_cotizacion=id_c, tipo=tipo,
                    valor_compra=compra, valor_venta=venta,
                    fecha=fecha,
                )
            )
        print("  [OK] Cotizaciones precargadas (10)")
