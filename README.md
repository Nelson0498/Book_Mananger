# Sprint 3: Book Manager con web scraping, reportes y auditoría

## Objetivo

El objetivo principal de este proyecto es aplicar los conocimientos adquiridos en
programación orientada a objetos, persistencia en bases de datos relacionales
mediante un ORM y obtención de datos de la web (web scraping) para analizarlos.

## Introducción y Contexto del problema

Una librería con venta al público necesita modernizar su sistema de gestión de
inventario de libros. Debido a la fluctuación en los costos de importación de
material bibliográfico, el sistema debe gestionar precios en diferentes monedas y
seguir de cerca la cotización del dólar para actualizar sus valores en tiempo real.

En el **Sprint 1** se desarrolló una aplicación de consola (CLI) en Python con las
entidades del dominio encapsuladas, una capa de servicios con la lógica de negocio
y repositorios que persistían en archivos CSV.

En el **Sprint 2** la aplicación pasó a persistir en una base de datos relacional
PostgreSQL (alojada en Supabase) utilizando **SQLAlchemy** como ORM, con una
migración reproducible de los datos y una **API externa** para obtener las
cotizaciones del dólar.

En el **Sprint 3** el sistema empieza a mirar hacia afuera: se descargan y obtienen
datos de la web para trabajar con ellos. La idea es obtener los precios de nuestros
competidores (librerías con venta online), en este caso [Cúspide](https://cuspide.com/),
y de esta forma poder compararnos con ellos y competir de forma más informada.
Para eso se incorpora:

- Un **scraper con Scrapy** (`CuspideSpider`) que busca cada título de nuestro
  catálogo —solo los 10 primeros resultados— y obtiene precio, imagen, formas de
  pago y descripción detallada, con *loaders* y *pipelines*.
- **Alertas de precios** en un archivo CSV descargable, con el umbral de diferencia
  ingresado por el usuario antes de cada ejecución.
- Un **reporte en Excel** que compara el precio interno con el precio web.
- Un **decorador de auditoría** que registra cada operación del sistema.
- Tres opciones nuevas de menú: ejecutar el scraping, generar el reporte y ver el
  historial de auditoría.

Además, se aplicaron las correcciones de las devoluciones de los Sprints 1 y 2: un
libro tiene **varios precios** (uno por moneda), `Stock` y `Precio` referencian al
objeto `Libro`, la lista bimonetaria admite cualquier moneda y el código cumple los
estándares de estilo (PEP 8, *type hints* y *docstrings*).

## Estructura del proyecto

```
book_manager/
├── src/
│   └── book_manager/
│       ├── database/
│       │   └── connection.py       # ConexionDB: motor, sesiones y transacciones
│       ├── entities/
│       │   └── entities.py         # Entidades del dominio
│       ├── models/
│       │   └── models.py           # Tablas del sistema (ORM SQLAlchemy)
│       ├── preload_data/
│       │   └── preload_data.py     # Carga de datos iniciales desde archivos .sql
│       ├── repositories/
│       │   └── repositories.py     # Repositorios SQLAlchemy
│       ├── schemas/
│       │   └── schemas.py          # Validación de entrada con Pydantic
│       ├── scraper/
│       │   ├── scrapy.cfg          # Proyecto Scrapy
│       │   └── cuspide/            # Spider, items, loaders, pipelines y settings
│       ├── services/
│       │   └── services.py         # Lógica de negocio y decorador de auditoría
│       ├── migrations/
│       │   ├── csv/                # Datos de origen (CSV)
│       │   ├── sql/                # Scripts .sql de datos generados desde los CSV
│       │   └── migrations.py       # Migración de CSV a SQL
│       ├── reportes/               # Reportes generados (alertas CSV y Excel)
│       ├── ui/
│       │   └── console.py          # Interfaz de consola
│       └── main.py                 # Punto de entrada
├── .env                            # Variables de entorno NO secretas (versionado)
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

### Modelo de datos

- **Libro 1 — N Precio:** cada libro tiene un precio por moneda
  (`UNIQUE(libro_id, moneda_id)`); el precio en pesos (ARS) es obligatorio.
- **Libro 1 — 1 Stock:** `stock.libro_id` es único.
- Las entidades se relacionan **por objeto**: `Precio.libro`, `Stock.libro`,
  `Libro.precios` y `Libro.stock`.
- Los libros se identifican con un `id` entero; el ISBN es único.

### Migraciones: estructura y datos

- **Estructura:** la crean los modelos ORM con `crear_tablas()`
  (`Base.metadata.create_all()`). Como `create_all` no modifica tablas ya
  existentes, si la base viene del Sprint 2 hay que ejecutar antes
  `recrear_tablas()` (**borra todos los datos**).
- **Datos:** `migrar_datos()` genera un script `.sql` por tabla desde los CSV y los
  escribe en `migrations/sql/`.

## Requisitos

- Python 3.11 o superior.
- PostgreSQL 14 o superior (se utiliza una instancia de Supabase).

```bash
python -m venv .venv
.venv/Scripts/activate      # En Linux o macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración del entorno

Las variables de entorno se leen con `python-dotenv` desde el archivo `.env` de la
raíz del proyecto. En este sprint el `.env` **se versiona**, pero solo contiene
variables que **no son secretas**.

| Variable | Descripción | ¿Secreta? | Dónde se define |
| --- | --- | --- | --- |
| `DATABASE_URL` | URL de conexión a PostgreSQL. | Sí | Secrets de Colab o variable de entorno |
| `API_URL` | Endpoint de la API de cotizaciones del dólar. | No | `.env` |
| `API_URL_MONEDAS` | Endpoint de la API de cotizaciones de otras monedas. | No | `.env` |

Contenido del `.env`:

```ini
API_URL=https://dolarapi.com/v1/dolares
API_URL_MONEDAS=https://dolarapi.com/v1/cotizaciones
```

`DATABASE_URL` **nunca** se escribe en un archivo versionado. En local se exporta en
la shell; en **Google Colab** se obtiene desde los *Secrets* del notebook:

```python
import os
from google.colab import userdata

os.environ["DATABASE_URL"] = userdata.get("DATABASE_URL")
```

El esquema `postgresql://` se normaliza automáticamente al driver `psycopg` (v3)
en `ConexionDB`.

## Ejecución

El proyecto utiliza el diseño `src/`, por lo que `src` debe estar en `PYTHONPATH`:

```bash
export PYTHONPATH=src          # En Windows PowerShell: $env:PYTHONPATH = "src"
python -m book_manager.main
```

Desde el notebook:

```python
from book_manager.main import main

main(import_default_data=False)
```

### Menú principal

| Opción | Acción |
| --- | --- |
| 1 a 8 | CRUD de Libros, Géneros, Editoriales, Monedas, Precios, Stock, Tipos de Cotización y Cotizaciones del Dólar. |
| 9 | Obtener las cotizaciones del dólar por API. |
| 10 | Lista de precios bimonetaria (pesos y la moneda elegida; para el USD se elige el tipo de cotización). |
| 11 | Exportar los precios a CSV, con una columna por moneda. |
| 12 | **Ejecutar scraping de Cúspide:** pide el umbral de diferencia (%), muestra un resumen y genera el CSV de alertas. |
| 13 | **Generar reporte Excel** con precio interno, precio web y diferencia. |
| 14 | **Ver historial de auditoría**, con filtro opcional por acción. |

Los archivos generados (`alertas_*.csv`, `precios_*.csv` y `reporte_precios_*.xlsx`)
se guardan en `src/book_manager/reportes/`; en Colab el menú ofrece descargarlos.

### Parámetro `import_default_data`

| Valor | Comportamiento |
| --- | --- |
| `True` (por defecto) | Asegura el esquema y carga los datos iniciales desde los scripts `.sql`. |
| `False` | No carga ningún dato: solo asegura que las tablas existan. |

## Scraper de Cúspide (Scrapy)

El proyecto Scrapy vive en `src/book_manager/scraper/` y contiene el spider
`CuspideSpider` (`name = "cuspide"`), el item `LibroWebItem`, el loader
`LibroWebLoader` y tres pipelines (validación, coincidencia y persistencia).

- **Qué busca:** solo los libros del catálogo propio. Por cada título se hace
  una búsqueda en Cúspide y se visitan los **10 primeros resultados**.
- **Qué obtiene:** precio, URL de la imagen, formas de pago con su precio y
  descripción detallada (más título, ISBN y URL de la ficha).
- **Dónde guarda:** en la tabla `precios_web`, sin borrar las extracciones
  anteriores. El pipeline de coincidencia marca como `coincide` los resultados
  cuyo ISBN es igual al interno o cuyo título se parece al menos un 75 %.
- **Cortesía con el sitio:** respeta `robots.txt`, se identifica con un
  `User-Agent` propio y limita la velocidad (`DOWNLOAD_DELAY = 1`).

La forma habitual de ejecutarlo es desde el menú (opción 12), que lanza Scrapy
en un subproceso. También puede correrse a mano; `DATABASE_URL` debe estar
definida y `libros.json` contiene `[{"id": 1, "titulo": "...", "isbn": "..."}]`:

```bash
cd src/book_manager/scraper
export PYTHONPATH=../..:.      # En Windows PowerShell: $env:PYTHONPATH = "../..;."
python -m scrapy crawl cuspide -a libros=libros.json
```

## Auditoría

Cada operación de los servicios queda registrada en la tabla `auditorias`
(`accion`, `fecha`, `detalles`) mediante el decorador `@auditar("VERBO_ENTIDAD")`
de `services.py`. Si la operación falla se registra `VERBO_ENTIDAD_ERROR` con el
mensaje del error y la excepción se vuelve a lanzar. Un fallo al auditar nunca
interrumpe la operación original. El historial se consulta desde el menú.

## Reglas de negocio

- **Precio en pesos obligatorio:** todo libro tiene un precio en ARS; no se puede
  eliminar.
- **Lista bimonetaria:** muestra el precio en pesos y en la moneda elegida. Si el
  libro ya tiene un precio cargado en esa moneda se usa ese; si no, se convierte
  con la cotización. Para el dólar el usuario elige **qué tipo de cotización**
  usar (Oficial por defecto); las demás monedas se toman de `API_URL_MONEDAS`.
  Las monedas sin cotización se muestran como `N/D`.
- **Cotizaciones duplicadas:** la API del dólar se registra una vez por tipo y fecha;
  volver a consultarla actualiza los valores existentes. Si la API informa un tipo
  que no existe, se crea automáticamente.

## Historial de sprints

| Sprint | Alcance | Persistencia |
| --- | --- | --- |
| 1 | Entidades, servicios, consola y CRUD completo. | Archivos CSV |
| 2 | Modelos ORM, migración de datos, API del dólar y reportes. | PostgreSQL (Supabase) vía SQLAlchemy |
| 3 | Web scraping de Cúspide, alertas, reporte Excel, auditoría y correcciones. | PostgreSQL (Supabase) vía SQLAlchemy |
