"""Carga de datos iniciales del sistema desde archivos SQL.

Los scripts `.sql` de `migrations/sql/` contienen sentencias `INSERT`
idempotentes (`ON CONFLICT DO NOTHING`), generadas desde los CSV por
`migrations.migrar_datos()`. Este módulo los ejecuta contra la base de datos,
uno por archivo y dentro de una transacción, en orden alfabético
(`01_...`, `02_...`), que respeta las dependencias entre tablas.
"""

import glob
import os
import re
from typing import List

from sqlalchemy import text

from book_manager.database.connection import ConexionDB

# Raíz del proyecto: preload_data/ -> book_manager/ -> src/ -> raíz.
_RAIZ_PROYECTO = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)

# Carpeta con los scripts SQL de datos.
CARPETA_SQL_DEFECTO = os.path.join(
    _RAIZ_PROYECTO, "src", "book_manager", "migrations", "sql"
)

# Sentencias de estructura que no deben ejecutarse al cargar datos: la
# creación de las tablas corresponde a SQLAlchemy (`crear_tablas()`). Solo se
# revisa el comienzo de cada sentencia para no confundirlas con textos de
# libros que contengan esas palabras.
_PATRON_ESTRUCTURA = re.compile(
    r"\s*(CREATE|ALTER|DROP|TRUNCATE)\b",
    re.IGNORECASE,
)


def _separar_sentencias(contenido: str) -> List[str]:
    """Divide el contenido de un script SQL en sentencias.

    Ignora las líneas de comentario (`--`) y separa por `;` únicamente fuera
    de las comillas simples, de modo que un `;` dentro de un texto no corte
    la sentencia.

    Args:
        contenido (str): Texto completo del script.

    Returns:
        List[str]: Sentencias sin el `;` final ni espacios sobrantes.
    """
    lineas = [
        linea for linea in contenido.splitlines()
        if not linea.strip().startswith("--")
    ]
    texto = "\n".join(lineas)

    sentencias: List[str] = []
    actual: List[str] = []
    entre_comillas = False

    for caracter in texto:
        if caracter == "'":
            entre_comillas = not entre_comillas
        if caracter == ";" and not entre_comillas:
            sentencia = "".join(actual).strip()
            if sentencia:
                sentencias.append(sentencia)
            actual = []
        else:
            actual.append(caracter)

    resto = "".join(actual).strip()
    if resto:
        sentencias.append(resto)

    return sentencias


def cargar_datos_desde_sql(conexion: ConexionDB, ruta_sql: str) -> int:
    """Ejecuta las sentencias INSERT de un archivo .sql en una transacción.

    Si alguna sentencia falla, se revierte todo el archivo.

    Args:
        conexion (ConexionDB): Conexión a la base de datos.
        ruta_sql (str): Ruta del archivo `.sql` a ejecutar.

    Returns:
        int: Cantidad de sentencias ejecutadas.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el archivo contiene sentencias de estructura
            (CREATE, ALTER, DROP o TRUNCATE).
    """
    if not os.path.isfile(ruta_sql):
        raise FileNotFoundError(f"No se encontró el archivo SQL: {ruta_sql}")

    with open(ruta_sql, mode="r", encoding="utf-8") as archivo:
        sentencias = _separar_sentencias(archivo.read())

    for sentencia in sentencias:
        if _PATRON_ESTRUCTURA.match(sentencia):
            raise ValueError(
                f"El script {os.path.basename(ruta_sql)} contiene "
                "sentencias de estructura (CREATE/ALTER/DROP/TRUNCATE). "
                "La carga de datos solo acepta inserciones: la estructura "
                "se crea mediante crear_tablas()."
            )

    with conexion.transaccion() as sesion:
        for sentencia in sentencias:
            # Los ':' se escapan para que `text()` no los tome como
            # parámetros enlazados dentro de los textos de los libros.
            sesion.execute(text(sentencia.replace(":", r"\:")))

    return len(sentencias)


def cargar_datos_iniciales(
    conexion: ConexionDB, carpeta_sqls: str = CARPETA_SQL_DEFECTO
) -> List[str]:
    """Carga todos los scripts `.sql` de una carpeta, en orden alfabético.

    Args:
        conexion (ConexionDB): Conexión a la base de datos.
        carpeta_sqls (str): Carpeta con los scripts (`01_...sql`, etc.).

    Returns:
        List[str]: Rutas de los scripts ejecutados, en orden de ejecución.

    Raises:
        FileNotFoundError: Si la carpeta no contiene scripts `.sql`.
    """
    rutas = sorted(glob.glob(os.path.join(carpeta_sqls, "*.sql")))

    if not rutas:
        raise FileNotFoundError(
            f"No se encontraron scripts .sql en {carpeta_sqls}. "
            "Ejecutá migrar_datos() para generarlos."
        )

    for ruta in rutas:
        cargar_datos_desde_sql(conexion, ruta)

    return rutas
