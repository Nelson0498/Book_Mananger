"""Loaders del scraper de Cúspide: limpieza de los datos extraídos."""

import re
from typing import Optional

from itemloaders.processors import Identity, Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader


def limpiar_precio(valor: str) -> Optional[float]:
    """Convierte un precio en formato argentino a número.

    Ejemplo: `"$\\xa038.999,00"` se convierte en `38999.0`.

    Args:
        valor (str): Texto del precio, con símbolo, miles y coma decimal.

    Returns:
        Optional[float]: El precio, o None si el texto no tiene un número.
    """
    texto = re.sub(r"[^\d,.]", "", valor or "")
    if not texto:
        return None
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def normalizar_espacios(valor: str) -> str:
    """Colapsa los espacios, tabulaciones y saltos de línea repetidos.

    Args:
        valor (str): Texto a normalizar.

    Returns:
        str: El texto con espacios simples y sin espacios en los extremos.
    """
    return re.sub(r"\s+", " ", valor).strip()


class LibroWebLoader(ItemLoader):
    """Loader de `LibroWebItem` con la limpieza de cada campo."""

    default_output_processor = TakeFirst()

    titulo_web_in = MapCompose(str.strip)
    isbn_web_in = MapCompose(str.strip)
    precio_web_in = MapCompose(limpiar_precio)
    precio_usd_web_in = MapCompose(limpiar_precio)
    descripcion_in = MapCompose(normalizar_espacios)
    descripcion_out = Join(" ")
    formas_pago_out = Identity()
