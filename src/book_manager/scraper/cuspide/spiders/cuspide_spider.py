"""Spider que busca los libros del catálogo en Cúspide y obtiene sus datos."""

import json
import re
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional
from urllib.parse import quote_plus

import scrapy
from scrapy.http import Response

from cuspide.items import LibroWebItem
from cuspide.loaders import LibroWebLoader, limpiar_precio, normalizar_espacios

# Cantidad de resultados de cada búsqueda que se visitan.
MAX_RESULTADOS = 10

# Títulos de sección de la ficha que contienen la descripción detallada.
SECCIONES_DESCRIPCION = ("descripcion", "descripción", "sinopsis", "resena",
                         "reseña")


class CuspideSpider(scrapy.Spider):
    """Busca por título cada libro del catálogo y visita los primeros
    resultados.

    Solo se buscan libros del catálogo propio, recibidos en un archivo JSON
    con la lista `[{"id": 1, "titulo": "...", "isbn": "..."}]`:

        scrapy crawl cuspide -a libros=ruta/libros.json

    Attributes:
        libros: Libros del catálogo a buscar.
        libros_por_id: Los mismos libros, indexados por id.
        fecha_extraccion: Momento común a todos los items de la ejecución.
    """

    name = "cuspide"
    allowed_domains = ["cuspide.com"]
    url_busqueda = "https://cuspide.com/?s={consulta}&post_type=product"

    def __init__(self, libros: Optional[str] = None, *args: Any,
                 **kwargs: Any) -> None:
        """Lee el archivo JSON con los libros a buscar.

        Args:
            libros (Optional[str]): Ruta del archivo JSON con los libros.

        Raises:
            ValueError: Si no se indica el archivo de libros.
        """
        super().__init__(*args, **kwargs)
        if not libros:
            raise ValueError("Falta el argumento -a libros=<ruta_json>")

        with open(libros, encoding="utf-8") as archivo:
            self.libros: List[Dict[str, Any]] = json.load(archivo)
        self.libros_por_id = {libro["id"]: libro for libro in self.libros}
        self.fecha_extraccion = datetime.now()

    async def start(self) -> AsyncIterator[scrapy.Request]:
        """Genera una búsqueda por título para cada libro del catálogo."""
        for libro in self.libros:
            yield scrapy.Request(
                self.url_busqueda.format(
                    consulta=quote_plus(libro["titulo"])
                ),
                callback=self.parse_busqueda,
                cb_kwargs={"libro": libro},
            )

    def parse_busqueda(self, response: Response,
                       libro: Dict[str, Any]) -> Iterator[Any]:
        """Procesa los resultados de la búsqueda de un título.

        Si el sitio redirige directo a una ficha (un único resultado) se
        procesa esa ficha como la posición 1; si no, se visitan las
        primeras `MAX_RESULTADOS` tarjetas.

        Args:
            response (Response): Respuesta de la búsqueda.
            libro (Dict[str, Any]): Libro del catálogo que se busca.

        Yields:
            Requests a las fichas de producto o items de la ficha directa.
        """
        if response.css("p.product-page-price"):
            yield from self.parse_producto(
                response, libro=libro, posicion=1, imagen_tarjeta=None
            )
            return

        tarjetas = response.css("div.product-small.col")[:MAX_RESULTADOS]
        for posicion, tarjeta in enumerate(tarjetas, start=1):
            url = tarjeta.css(
                "a.woocommerce-LoopProduct-link::attr(href)"
            ).get() or tarjeta.css("a[href*='/producto/']::attr(href)").get()
            if not url:
                continue
            yield response.follow(
                url,
                callback=self.parse_producto,
                cb_kwargs={
                    "libro": libro,
                    "posicion": posicion,
                    "imagen_tarjeta": tarjeta.css(
                        "div.box-image img::attr(src)"
                    ).get(),
                },
            )

    def parse_producto(self, response: Response, libro: Dict[str, Any],
                       posicion: int,
                       imagen_tarjeta: Optional[str]) -> Iterator[Any]:
        """Extrae los datos de la ficha de un producto.

        Args:
            response (Response): Respuesta de la ficha.
            libro (Dict[str, Any]): Libro del catálogo que se busca.
            posicion (int): Posición del resultado en la búsqueda.
            imagen_tarjeta (Optional[str]): Imagen de la tarjeta de la
                búsqueda, usada si la ficha no trae una.

        Yields:
            LibroWebItem: El item con los datos de la ficha.
        """
        loader = LibroWebLoader(item=LibroWebItem(), response=response)
        loader.add_value("libro_id", libro["id"])
        loader.add_value("posicion", posicion)
        loader.add_value("url", response.url)
        loader.add_value("fecha_extraccion", self.fecha_extraccion)
        loader.add_css("titulo_web", "h1.product-title::text")
        loader.add_css("isbn_web", "span.sku::text")
        loader.add_css("precio_web", "p.product-page-price bdi::text")
        loader.add_xpath(
            "precio_usd_web", "//span[contains(text(),'U$s')]/span/text()"
        )

        if not loader.get_collected_values("precio_web"):
            loader.add_value("precio_web", self._precio_json_ld(response))

        loader.add_value("url_imagen", self._imagen(response, imagen_tarjeta))
        loader.add_value("formas_pago", self._formas_pago(response))
        loader.add_value("descripcion", self._descripcion(response))

        yield loader.load_item()

    @staticmethod
    def _json_ld_producto(response: Response) -> Dict[str, Any]:
        """Devuelve el objeto `Product` del JSON-LD de la página, si existe.

        Args:
            response (Response): Respuesta de la ficha.

        Returns:
            Dict[str, Any]: El producto, o un diccionario vacío.
        """
        for texto in response.css(
            'script[type="application/ld+json"]::text'
        ).getall():
            try:
                datos = json.loads(texto)
            except ValueError:
                continue
            candidatos = datos.get("@graph", [datos]) if isinstance(
                datos, dict) else datos
            for candidato in candidatos:
                if isinstance(candidato, dict) and \
                        candidato.get("@type") == "Product":
                    return candidato
        return {}

    def _precio_json_ld(self, response: Response) -> Optional[str]:
        """Obtiene el precio del JSON-LD, usado si falla el selector CSS.

        Returns:
            Optional[str]: El precio en formato argentino (con coma decimal,
            para que lo limpie el loader), o None.
        """
        ofertas = self._json_ld_producto(response).get("offers")
        if isinstance(ofertas, list):
            ofertas = ofertas[0] if ofertas else None
        if not isinstance(ofertas, dict) or "price" not in ofertas:
            return None
        try:
            return f"{float(ofertas['price']):.2f}".replace(".", ",")
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _imagen(response: Response,
                imagen_tarjeta: Optional[str]) -> Optional[str]:
        """Obtiene la URL de la imagen del producto.

        Args:
            response (Response): Respuesta de la ficha.
            imagen_tarjeta (Optional[str]): Imagen de la tarjeta de búsqueda.

        Returns:
            Optional[str]: La primera imagen disponible, o None.
        """
        return (
            response.css(
                "div.woocommerce-product-gallery__image::attr(data-thumb)"
            ).get()
            or response.css(
                "img.wp-post-image::attr(data-large_image)"
            ).get()
            or imagen_tarjeta
        )

    @staticmethod
    def _formas_pago(response: Response) -> List[Dict[str, Any]]:
        """Obtiene las formas de pago con el precio de lista.

        El sitio no informa un precio distinto por medio de pago, por lo que
        a cada forma se le asigna el precio en pesos de la ficha.

        Args:
            response (Response): Respuesta de la ficha.

        Returns:
            List[Dict[str, Any]]: Una entrada `{"forma", "precio"}` por cada
            forma de pago.
        """
        precio = limpiar_precio(
            response.css("p.product-page-price bdi::text").get() or ""
        )
        formas = []
        for item in response.css("#contentPaymentsPopUpArg li"):
            texto = normalizar_espacios(" ".join(item.css("*::text").getall()))
            texto = re.sub(r"^>\s*", "", texto)
            if texto:
                formas.append({"forma": texto, "precio": precio})
        return formas

    def _descripcion(self, response: Response) -> List[str]:
        """Obtiene la descripción detallada del producto.

        Busca la sección de descripción o sinopsis; si no existe, usa la tabla
        de especificaciones y, como último recurso, la descripción del
        JSON-LD.

        Args:
            response (Response): Respuesta de la ficha.

        Returns:
            List[str]: Fragmentos de texto que el loader une en uno solo.
        """
        for seccion in response.css("div.product-section"):
            titulo = normalizar_espacios(
                " ".join(seccion.css("h5 *::text, h5::text").getall())
            ).lower()
            if titulo in SECCIONES_DESCRIPCION:
                texto = seccion.css("div.panel *::text").getall()
                if any(t.strip() for t in texto):
                    return texto

        filas = []
        for fila in response.css("table.shop_attributes tr"):
            clave = normalizar_espacios(
                " ".join(fila.css("th *::text, th::text").getall())
            )
            valor = normalizar_espacios(
                " ".join(fila.css("td *::text, td::text").getall())
            )
            if clave and valor:
                filas.append(f"{clave}: {valor}")
        if filas:
            return [" | ".join(filas)]

        descripcion = self._json_ld_producto(response).get("description")
        return [descripcion] if descripcion else []
