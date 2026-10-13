
"""Administración de conexiones y transacciones de PostgreSQL."""

import os
from contextlib import contextmanager
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker


# Raíz del proyecto: database/ -> book_manager/ -> src/ -> raíz.
_RAIZ_PROYECTO = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)

# Carga las variables definidas en el archivo .env de la raíz del proyecto.
# Se indica la ruta de forma explícita: la búsqueda automática de python-dotenv
# depende de la pila de llamadas y falla al ejecutar desde stdin o un REPL.
load_dotenv(dotenv_path=os.path.join(_RAIZ_PROYECTO, ".env"))

# Esquemas de URL de PostgreSQL que se normalizan al driver psycopg (v3).
_ESQUEMA_POSTGRES = "postgresql://"
_ESQUEMA_POSTGRES_PSYCOPG = "postgresql+psycopg://"

# Segundos tras los cuales el pool descarta una conexión ociosa. El pooler de
# Supabase cierra las conexiones inactivas, por lo que conviene reciclarlas.
_RECICLADO_POOL_SEGUNDOS = 300

# Segundos de espera máxima al establecer una conexión nueva.
_ESPERA_CONEXION_SEGUNDOS = 10


def normalizar_url(database_url: str) -> str:
    """Garantiza el driver psycopg (v3) en las URL de PostgreSQL.

    SQLAlchemy resuelve las URL con esquema ``postgresql://`` de forma distinta
    según su versión: psycopg2 en la línea 2.0 y psycopg (v3) desde la 2.1.
    Como el proyecto declara ``psycopg[binary]`` en requirements.txt, la URL se
    normaliza para que el driver sea siempre el mismo, sin depender de la
    versión instalada ni del formato provisto por el entorno.

    Args:
        database_url (str): URL de conexión tal como llega desde el entorno.

    Returns:
        str: La URL con el driver psycopg explícito, o sin cambios si ya lo
        incluye o si no corresponde a PostgreSQL.
    """
    if database_url.startswith(_ESQUEMA_POSTGRES):
        return _ESQUEMA_POSTGRES_PSYCOPG + database_url[len(_ESQUEMA_POSTGRES):]
    return database_url


class ConexionDB:
    """Administra el motor y las sesiones de SQLAlchemy."""

    def __init__(self, database_url: str | None = None) -> None:
        url = normalizar_url(database_url or os.getenv("DATABASE_URL", ""))

        if not url:
            raise ValueError(
                "No se encontró DATABASE_URL. Revisá el archivo .env o "
                "configurá el secreto correspondiente en el entorno."
            )

        # connect_timeout es propio de PostgreSQL: otros motores, como SQLite
        # en las pruebas automatizadas, no aceptan ese argumento.
        argumentos_conexion: dict[str, int] = {}
        if url.startswith("postgresql"):
            argumentos_conexion["connect_timeout"] = _ESPERA_CONEXION_SEGUNDOS

        self._engine: Engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=_RECICLADO_POOL_SEGUNDOS,
            connect_args=argumentos_conexion,
        )

        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> Engine:
        """Devuelve el motor de SQLAlchemy."""
        return self._engine

    @contextmanager
    def obtener_sesion(self) -> Iterator[Session]:
        """Proporciona una sesión de consulta y garantiza su cierre.

        Está pensada para lecturas: no confirma cambios, por lo que cualquier
        escritura realizada a través de este context manager se descarta al
        cerrar la sesión. Para escribir debe usarse `transaccion()`.

        Yields:
            Session: Sesión de SQLAlchemy lista para consultar.
        """
        sesion = self._session_factory()

        try:
            yield sesion
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()

    @contextmanager
    def transaccion(self) -> Iterator[Session]:
        """Ejecuta operaciones de escritura dentro de una transacción.

        Confirma (commit) al salir del bloque si todo sale bien y revierte
        (rollback) ante cualquier excepción; la sesión se cierra siempre.

        Yields:
            Session: Sesión de SQLAlchemy lista para escribir.
        """
        with self._session_factory.begin() as sesion:
            yield sesion

    def probar_conexion(self) -> bool:
        """Comprueba la conectividad con la base de datos.

        Returns:
            bool: True si la base respondió a una consulta trivial.
        """
        with self._engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))

        return True

    def cerrar(self) -> None:
        """Libera las conexiones del motor."""
        self._engine.dispose()
