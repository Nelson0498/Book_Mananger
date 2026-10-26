"""Pipelines del scraper de Cúspide: validación, coincidencia y persistencia.

Se ejecutan en este orden: se descartan los items incompletos, se marca si el
resultado es el mismo libro del catálogo y se guarda en la base de datos.
"""

import difflib
import json
import re
import unicodedata
from datetime import datetime
from typing import Dict, Optional

from scrapy.crawler import Crawler
from scrapy.exceptions import DropItem

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import Libro, PrecioWeb
from book_manager.repositories.repositories import (
    RepositorioLibro,
    RepositorioPrecioWeb,
)

# Similitud mínima entre títulos para considerar que es el mismo libro.
UMBRAL_SIMILITUD = 0.75


def normalizar(texto: Optional[str]) -> str:
    """Pasa a minúsculas, quita acentos y puntuación y colapsa espacios.

    Args:
        texto (Optional[str]): Texto a normalizar.

    Returns:
        str: El texto normalizado, apto para comparar.
    """
    descompuesto = unicodedata.normalize("NFKD", (texto or "").lower())
    sin_acentos = "".join(
        c for c in descompuesto if not unicodedata.combining(c)
    )
    return re.sub(r"[^a-z0-9]+", " ", sin_acentos).strip()


def solo_digitos(texto: Optional[str]) -> str:
    """Devuelve únicamente los dígitos de un texto (por ejemplo, un ISBN)."""
    return re.sub(r"\D", "", texto or "")


class _PipelineBase:
    """Base de los pipelines: guarda el crawler que los crea."""

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "_PipelineBase":
        """Crea el pipeline conservando el crawler.

        Args:
            crawler (Crawler): Crawler de Scrapy; da acceso al spider.

        Returns:
            _PipelineBase: La instancia del pipeline.
        """
        pipeline = cls()
        pipeline.crawler = crawler
        return pipeline


class ValidacionPipeline(_PipelineBase):
    """Descarta los items sin precio o sin URL."""

    def process_item(self, item):
        """Valida el item.

        Args:
            item: Item extraído por el spider.

        Returns:
            El mismo item, si es válido.

        Raises:
            DropItem: Si no tiene precio o URL.
        """
        if item.get("precio_web") is None:
            raise DropItem(f"Sin precio: {item.get('url')}")
        if not item.get("url"):
            raise DropItem("Sin URL")
        return item


class CoincidenciaPipeline(_PipelineBase):
    """Marca si el resultado web es el mismo libro del catálogo.

    Hay coincidencia si el ISBN informado por el sitio es igual al interno
    (solo dígitos) o si los títulos normalizados se parecen al menos en
    `UMBRAL_SIMILITUD`. Se guarda también la similitud para que el servicio
    pueda quedarse con la mejor coincidencia de cada libro.
    """

    def process_item(self, item):
        """Completa `coincide` y `similitud` en el item.

        Args:
            item: Item extraído por el spider.

        Returns:
            El item con los campos de coincidencia completos.
        """
        libro = self.crawler.spider.libros_por_id[item["libro_id"]]

        isbn_web = solo_digitos(item.get("isbn_web"))
        isbn_interno = solo_digitos(libro.get("isbn"))
        similitud = difflib.SequenceMatcher(
            None,
            normalizar(item.get("titulo_web")),
            normalizar(libro["titulo"]),
        ).ratio()

        mismo_isbn = bool(isbn_web) and isbn_web == isbn_interno
        item["similitud"] = 1.0 if mismo_isbn else round(similitud, 4)
        item["coincide"] = mismo_isbn or similitud >= UMBRAL_SIMILITUD
        return item


class PersistenciaPipeline(_PipelineBase):
    """Guarda cada item en la tabla `precios_web`."""

    def open_spider(self):
        """Abre la conexión a la base de datos al iniciar el spider."""
        self._conexion = ConexionDB()
        self._repositorio = RepositorioPrecioWeb(self._conexion)
        self._repositorio_libro = RepositorioLibro(self._conexion)
        self._libros: Dict[int, Libro] = {}

    def close_spider(self):
        """Cierra la conexión a la base de datos al terminar el spider."""
        self._conexion.cerrar()

    def process_item(self, item):
        """Persiste el item como un `PrecioWeb`.

        Args:
            item: Item validado y con la coincidencia calculada.

        Returns:
            El mismo item.
        """
        libro_id = item["libro_id"]
        if libro_id not in self._libros:
            self._libros[libro_id] = self._repositorio_libro.leer_por_id(
                libro_id
            )

        formas_pago = item.get("formas_pago")
        self._repositorio.crear(PrecioWeb(
            libro=self._libros[libro_id],
            posicion=item["posicion"],
            titulo_web=item["titulo_web"][:300],
            url=item["url"][:500],
            precio_web=item["precio_web"],
            fecha_extraccion=item.get("fecha_extraccion", datetime.now()),
            isbn_web=item.get("isbn_web"),
            url_imagen=item.get("url_imagen"),
            formas_pago=(
                json.dumps(formas_pago, ensure_ascii=False)
                if formas_pago else None
            ),
            descripcion=item.get("descripcion"),
            coincide=item.get("coincide", False),
            similitud=item.get("similitud"),
        ))
        return item
