"""Migración de los datos del Sprint 1 a la base de datos relacional.

La estructura de las tablas se crea mediante SQLAlchemy a partir de los
modelos definidos en models/models.py.

Este módulo lee los archivos CSV de migrations/csv, genera scripts SQL
con sentencias INSERT y los ejecuta en la base de datos.

Los scripts SQL generados se guardan en migrations/sql/ y se versionan.

Las sentencias de inserción son idempotentes: utilizan ON CONFLICT DO NOTHING
para evitar duplicar registros cuando se repite la migración.

El orden de las tablas respeta las dependencias de claves foráneas.

Los CSV se leen como UTF-8, con o sin BOM, y los scripts se escriben en UTF-8
para conservar correctamente los acentos y la ñ.
"""

import csv
import glob
import os
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Tuple

from sqlalchemy import text

from book_manager.database.connection import ConexionDB
from book_manager.models.models import Base


# Raíz del proyecto: migrations/ -> book_manager/ -> src/ -> raíz.
_RAIZ_PROYECTO = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)

# Carpeta de archivos CSV originales del Sprint 1.
CARPETA_CSV_POR_DEFECTO = os.path.join(
    _RAIZ_PROYECTO, "src", "book_manager", "migrations", "csv"
)

# Carpeta de scripts SQL de datos, generados a partir de los CSV.
CARPETA_SQL_POR_DEFECTO = os.path.join(
    _RAIZ_PROYECTO, "src", "book_manager", "migrations", "sql"
)


# Sentencias de estructura que no deben ejecutarse durante la migración
# de datos. La creación de tablas corresponde a SQLAlchemy.
_PATRON_ESTRUCTURA = re.compile(
    r"\b(CREATE|ALTER|DROP|TRUNCATE)\s+"
    r"(TABLE|INDEX|SCHEMA|VIEW|SEQUENCE)",
    re.IGNORECASE,
)

# Tipos de datos admitidos en las columnas de origen.
TEXTO = "texto"
TEXTO_OPCIONAL = "texto_opcional"
ENTERO = "entero"
DECIMAL = "decimal"
FECHA = "fecha"


@dataclass(frozen=True)
class DefinicionTabla:
    """Describe el CSV de origen, la tabla destino y los tipos de columnas."""

    tabla: str
    archivo_csv: str
    columnas: Tuple[str, ...]
    tipos: Tuple[str, ...]


# Tablas ordenadas según sus dependencias de claves foráneas.
DEFINICIONES_TABLAS: Tuple[DefinicionTabla, ...] = (
    DefinicionTabla(
        tabla="generos",
        archivo_csv="generos.csv",
        columnas=("id", "nombre"),
        tipos=(ENTERO, TEXTO),
    ),
    DefinicionTabla(
        tabla="editoriales",
        archivo_csv="editoriales.csv",
        columnas=("id", "nombre", "pais"),
        tipos=(ENTERO, TEXTO, TEXTO_OPCIONAL),
    ),
    DefinicionTabla(
        tabla="monedas",
        archivo_csv="monedas.csv",
        columnas=("id", "codigo", "nombre", "simbolo"),
        tipos=(ENTERO, TEXTO, TEXTO, TEXTO),
    ),
    DefinicionTabla(
        tabla="tipos_cotizacion",
        archivo_csv="tipos_cotizacion.csv",
        columnas=("id", "nombre"),
        tipos=(ENTERO, TEXTO),
    ),
    DefinicionTabla(
        tabla="libros",
        archivo_csv="libros.csv",
        columnas=(
            "id",
            "isbn",
            "titulo",
            "autor",
            "editorial_id",
            "genero_id",
        ),
        tipos=(ENTERO, TEXTO, TEXTO, TEXTO, ENTERO, ENTERO),
    ),
    DefinicionTabla(
        tabla="precios",
        archivo_csv="precios.csv",
        columnas=("id", "libro_id", "moneda_id", "valor"),
        tipos=(ENTERO, ENTERO, ENTERO, DECIMAL),
    ),
    DefinicionTabla(
        tabla="stock",
        archivo_csv="stock.csv",
        columnas=("id_stock", "libro_id", "cantidad", "cantidad_minima"),
        tipos=(ENTERO, ENTERO, ENTERO, ENTERO),
    ),
    DefinicionTabla(
        tabla="cotizaciones",
        archivo_csv="cotizaciones.csv",
        columnas=(
            "id_cotizacion",
            "tipo_id",
            "valor_compra",
            "valor_venta",
            "fecha",
        ),
        tipos=(ENTERO, ENTERO, DECIMAL, DECIMAL, FECHA),
    ),
)


def _formatear_literal(valor: str, tipo: str) -> str:
    """Convierte un valor CSV en un literal SQL validado."""

    limpio = valor.strip()

    if tipo == TEXTO_OPCIONAL and limpio == "":
        return "NULL"

    if limpio == "":
        raise ValueError(
            "Se encontró un valor vacío en una columna obligatoria."
        )

    if tipo in (TEXTO, TEXTO_OPCIONAL):
        return "'" + limpio.replace("'", "''") + "'"

    if tipo == ENTERO:
        return str(int(limpio))

    if tipo == DECIMAL:
        return str(Decimal(limpio))

    if tipo == FECHA:
        return "'" + date.fromisoformat(limpio).isoformat() + "'"

    raise ValueError(f"Tipo de dato desconocido: {tipo}")


def _leer_filas_csv(
    ruta_csv: str,
    definicion: DefinicionTabla,
) -> List[Dict[str, str]]:
    """Lee el CSV y valida que sus columnas coincidan con las esperadas."""

    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"No se encontró el archivo CSV: {ruta_csv}")

    with open(
        ruta_csv,
        mode="r",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:
        lector = csv.DictReader(archivo)
        columnas_csv = tuple(lector.fieldnames or ())

        if set(columnas_csv) != set(definicion.columnas):
            raise ValueError(
                f"Las columnas de {os.path.basename(ruta_csv)} no coinciden "
                f"con las de la tabla {definicion.tabla}. "
                f"Esperadas: {sorted(definicion.columnas)}. "
                f"Encontradas: {sorted(columnas_csv)}."
            )

        return [dict(fila) for fila in lector]


def _construir_insert(
    definicion: DefinicionTabla,
    filas: List[Dict[str, str]],
) -> str:
    """Construye una sentencia INSERT idempotente para una tabla."""

    encabezado = [
        f"-- Migración de {definicion.archivo_csv} a la tabla "
        f"{definicion.tabla}.",
        "-- Script generado automáticamente por migrations.py.",
        "-- ON CONFLICT DO NOTHING evita duplicar registros.",
    ]

    if not filas:
        encabezado.append("-- El archivo de origen no contiene registros.")
        return "\n".join(encabezado) + "\n"

    valores = []

    for fila in filas:
        literales = [
            _formatear_literal(fila[columna], tipo)
            for columna, tipo in zip(
                definicion.columnas,
                definicion.tipos,
            )
        ]
        valores.append(f"    ({', '.join(literales)})")

    sentencia = [
        *encabezado,
        f"INSERT INTO {definicion.tabla} "
        f"({', '.join(definicion.columnas)}) VALUES",
        ",\n".join(valores),
        "ON CONFLICT DO NOTHING;",
    ]

    return "\n".join(sentencia) + "\n"


def migrar_datos(
    carpeta_csvs: str,
    carpeta_sqls: str,
) -> List[str]:
    """
    Genera los scripts SQL de inserción a partir de los CSV.

    Args:
        carpeta_csvs: Carpeta con los CSV originales.
        carpeta_sqls: Carpeta donde se guardarán los scripts SQL.

    Returns:
        Rutas de los archivos SQL generados, en orden de ejecución.
    """

    os.makedirs(carpeta_sqls, exist_ok=True)
    rutas_generadas: List[str] = []

    for indice, definicion in enumerate(DEFINICIONES_TABLAS, start=1):
        ruta_csv = os.path.join(
            carpeta_csvs,
            definicion.archivo_csv,
        )

        filas = _leer_filas_csv(ruta_csv, definicion)
        sentencia = _construir_insert(definicion, filas)

        ruta_sql = os.path.join(
            carpeta_sqls,
            f"{indice:02d}_{definicion.tabla}.sql",
        )

        with open(
            ruta_sql,
            mode="w",
            encoding="utf-8",
            newline="\n",
        ) as archivo:
            archivo.write(sentencia)

        rutas_generadas.append(ruta_sql)

    return rutas_generadas


def _leer_sentencia(ruta_sql: str) -> str | None:
    """Lee un script SQL y elimina las líneas de comentarios."""

    with open(ruta_sql, mode="r", encoding="utf-8") as archivo:
        lineas = [
            linea
            for linea in archivo.read().splitlines()
            if not linea.strip().startswith("--")
        ]

    sentencia = "\n".join(lineas).strip()
    return sentencia or None


def crear_tablas(conexion: ConexionDB) -> None:
    """Crea las tablas que todavía no existan.

    Args:
        conexion: Conexión a la base de datos.
    """

    Base.metadata.create_all(conexion.engine)


def recrear_tablas(conexion: ConexionDB) -> None:
    """Elimina todas las tablas del sistema y las vuelve a crear.

    `create_all` no altera las tablas que ya existen, por lo que al cambiar
    el esquema (por ejemplo, de Sprint 2 a Sprint 3) hay que recrearlas.
    Esta operación **borra todos los datos**: debe usarse solo con la
    confirmación explícita del usuario.

    Args:
        conexion: Conexión a la base de datos.
    """

    Base.metadata.drop_all(conexion.engine)
    Base.metadata.create_all(conexion.engine)


def aplicar_migracion(
    conexion: ConexionDB,
    carpeta_sqls: str,
) -> Dict[str, int]:
    """
    Ejecuta los scripts SQL dentro de una única transacción.

    Si un script falla, la transacción completa se revierte.
    """

    rutas = sorted(
        glob.glob(os.path.join(carpeta_sqls, "*.sql"))
    )

    if not rutas:
        raise FileNotFoundError(
            f"No se encontraron scripts .sql en {carpeta_sqls}. "
            "Ejecutá migrar_datos() para generarlos."
        )

    resultado: Dict[str, int] = {}

    with conexion.transaccion() as sesion:
        for ruta in rutas:
            sentencia = _leer_sentencia(ruta)

            if sentencia is None:
                resultado[os.path.basename(ruta)] = 0
                continue

            if _PATRON_ESTRUCTURA.search(sentencia):
                raise ValueError(
                    f"El script {os.path.basename(ruta)} contiene "
                    "sentencias de estructura (CREATE/ALTER/DROP/TRUNCATE). "
                    "La migración de datos solo acepta inserciones. "
                    "La estructura se crea mediante crear_tablas()."
                )

            resultado[os.path.basename(ruta)] = sesion.execute(
                text(sentencia)
            ).rowcount

    return resultado


def migrar_base_de_datos(
    conexion: ConexionDB,
    carpeta_csvs: str = CARPETA_CSV_POR_DEFECTO,
    carpeta_sqls: str = CARPETA_SQL_POR_DEFECTO,
) -> Dict[str, int]:
    """
    Crea las tablas, genera los scripts SQL y migra los datos.

    Args:
        conexion: Conexión a la base de datos.
        carpeta_csvs: Carpeta con los CSV de origen.
        carpeta_sqls: Carpeta para generar y ejecutar los scripts SQL.

    Returns:
        Cantidad de filas insertadas por cada script aplicado.
    """

    crear_tablas(conexion)
    migrar_datos(carpeta_csvs, carpeta_sqls)

    return aplicar_migracion(conexion, carpeta_sqls)
