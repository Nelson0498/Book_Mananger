"""Configuración del proyecto Scrapy de Cúspide."""

BOT_NAME = "cuspide"

SPIDER_MODULES = ["cuspide.spiders"]
NEWSPIDER_MODULE = "cuspide.spiders"

# Se respeta el robots.txt del sitio y se identifica al cliente.
ROBOTSTXT_OBEY = True
USER_AGENT = "BookManager/3.0 (TP Integrador UGR)"

# Se limita la carga sobre el sitio.
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 4
AUTOTHROTTLE_ENABLED = True

ITEM_PIPELINES = {
    "cuspide.pipelines.ValidacionPipeline": 100,
    "cuspide.pipelines.CoincidenciaPipeline": 200,
    "cuspide.pipelines.PersistenciaPipeline": 300,
}

FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
