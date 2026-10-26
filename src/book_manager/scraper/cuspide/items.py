"""Items del scraper de Cúspide."""

import scrapy


class LibroWebItem(scrapy.Item):
    """Datos de un libro obtenidos de la ficha de producto de Cúspide.

    Attributes:
        libro_id: Id del libro del catálogo con el que se buscó.
        posicion: Posición del resultado en la búsqueda (1..10).
        titulo_web: Título informado por el sitio.
        isbn_web: ISBN informado por el sitio.
        url: URL de la ficha del producto.
        precio_web: Precio en pesos.
        precio_usd_web: Precio en dólares informado por el sitio.
        url_imagen: URL de la imagen del producto.
        formas_pago: Lista de formas de pago con su precio.
        descripcion: Descripción detallada.
        fecha_extraccion: Momento de la extracción.
        similitud: Parecido del título con el del catálogo (0 a 1).
        coincide: True si el resultado es el mismo libro del catálogo.
    """

    libro_id = scrapy.Field()
    posicion = scrapy.Field()
    titulo_web = scrapy.Field()
    isbn_web = scrapy.Field()
    url = scrapy.Field()
    precio_web = scrapy.Field()
    precio_usd_web = scrapy.Field()
    url_imagen = scrapy.Field()
    formas_pago = scrapy.Field()
    descripcion = scrapy.Field()
    fecha_extraccion = scrapy.Field()
    similitud = scrapy.Field()
    coincide = scrapy.Field()
