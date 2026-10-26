# Sprint 3

[Ejercicio 06]
- Nueva tabla `auditorias` (`AuditoriaModel`) con `accion`, `fecha` y `detalles`, la entidad `Auditoria` y el `RepositorioAuditoria` (`crear`, `leer_todos(limite)` y `leer_por_accion`, del más reciente al más antiguo).
- `ServicioAuditoria` con `registrar`, `listar` y `listar_por_accion`. No se audita a sí mismo.
- Decorador `@auditar("VERBO_ENTIDAD")` en `services.py`: registra cada ejecución del método decorado y, si falla, registra `<ACCION>_ERROR` con el mensaje y relanza el error. Los detalles incluyen la clase, el método, los argumentos y se recortan a 1000 caracteres.
- Clase base `ServicioBase` que recibe el `ServicioAuditoria` (opcional) y expone `_registrar_auditoria`, que nunca propaga errores de auditoría.
- Todos los métodos públicos de todos los servicios están auditados (CRUD, cotizaciones por API, lista bimonetaria, exportación a CSV, scraping, alertas y reporte Excel).
- `main.py` crea primero el repositorio y el servicio de auditoría y se los pasa a todos los servicios.

[Ejercicio 05]
- Nuevo `ServicioReportes.generar_reporte_excel()`: arma un `DataFrame` de pandas y lo escribe con `to_excel(engine="openpyxl")` en `reportes/reporte_precios_YYYYMMDD_HHMMSS.xlsx`.
- Columnas: `Libro`, `Precio interno`, `Precio web`, `Diferencia` y `Fecha de extracción` (formato `AAAA-MM-DD HH:MM`), con una fila por cada libro con coincidencia en la última extracción. Se ajusta el ancho de las columnas con openpyxl.
- El cálculo del precio interno y de la diferencia se comparte con las alertas del Ejercicio 04 mediante la clase base `_ComparadorPrecios` y su método `_comparar_precios()`, que devuelve una lista de `ComparacionPrecio`.
- La consola ofrece generar el reporte y descargarlo cuando se ejecuta en Colab.

[Ejercicio 04]
- Comparación del precio interno (pesos; si el libro no tiene, se convierte el de dólares con la cotización Oficial) con el precio web de la mejor coincidencia de cada libro: la de mayor similitud de título y, ante un empate, la primera de la búsqueda.
- `ServicioScraping.generar_alertas(umbral_pct, fecha)`: escribe `reportes/alertas_YYYYMMDD_HHMMSS.csv` con `libro_id`, `isbn`, `titulo`, `precio_interno`, `precio_web`, `diferencia`, `diferencia_pct`, `tipo_alerta` (`MAS_CARO_WEB` o `MAS_BARATO_WEB`), `url` y `fecha_extraccion`.
- Hay alerta cuando la diferencia absoluta alcanza el umbral. El archivo se genera en cada ejecución del scraper, aunque no haya alertas (solo el encabezado).
- `ServicioScraping.ejecutar(umbral_pct)` pasa a recibir el umbral y devuelve el resumen con la cantidad de alertas y la ruta del CSV.
- La consola pide el umbral en % (validado con `pedir_float` y mayor que cero) antes de cada scraping, muestra la ruta absoluta del CSV y, si se ejecuta en Colab, ofrece descargarlo con `google.colab.files`.

[Ejercicio 03]
- Proyecto Scrapy en `scraper/` con el spider `CuspideSpider`: busca por título cada libro del catálogo en Cúspide (`/?s=<título>&post_type=product`) y visita los 10 primeros resultados; si la búsqueda redirige a una ficha, la procesa como resultado 1.
- Extracción de precio (con respaldo en el JSON-LD), URL de la imagen, formas de pago con su precio, descripción detallada (sección de descripción, tabla de especificaciones o JSON-LD), ISBN y título.
- `LibroWebItem` y `LibroWebLoader` con procesadores de entrada y salida (`limpiar_precio` convierte `"$ 38.999,00"` en `38999.0`).
- Pipelines: `ValidacionPipeline` descarta items sin precio o URL, `CoincidenciaPipeline` marca el mismo libro por ISBN o por similitud de título (≥ 75 %) y `PersistenciaPipeline` guarda en la base de datos.
- Configuración responsable: `ROBOTSTXT_OBEY`, `User-Agent` propio, `DOWNLOAD_DELAY = 1` y `AUTOTHROTTLE`.
- Nueva tabla `precios_web` (`PrecioWebModel`), entidad `PrecioWeb` y `RepositorioPrecioWeb` (`crear`, `leer_por_libro`, `leer_desde`, `leer_ultima_extraccion`). Se agrega la columna `similitud` para poder elegir la mejor coincidencia de cada libro.
- `ServicioScraping.ejecutar()` ejecuta Scrapy en un subproceso (el reactor de Twisted no se puede reiniciar en el mismo proceso) y devuelve un `ResultadoScraping`.
- `requirements.txt` pide `scrapy>=2.13`, versión desde la que los pipelines no reciben el spider por parámetro.

[Ejercicio 02]
- Reescritura de `preload_data/preload_data.py`: ya no usa repositorios CSV, ahora carga los datos desde archivos `.sql`.
- Nueva función `cargar_datos_desde_sql(conexion, ruta_sql)`: ejecuta las sentencias de un script en una transacción, separándolas por `;` fuera de comillas e ignorando comentarios; rechaza las sentencias de estructura (`CREATE`, `ALTER`, `DROP`, `TRUNCATE`).
- Nueva función `cargar_datos_iniciales(conexion, carpeta_sqls)`: recorre los `.sql` en orden alfabético y los carga.
- `aplicar_migracion()` pasa a delegar en `cargar_datos_iniciales()` para no duplicar lógica.
- `main(import_default_data)`: con `True` crea las tablas, genera los scripts desde los CSV y los carga; con `False` solo crea las tablas.
- Se versionan los scripts `.sql` regenerados en `migrations/sql/` con el nuevo esquema.

[Ejercicio 01]
- Creación de la rama `Sprint_3` a partir de `Sprint_2`.
- Actualización de `README.md` con el objetivo, la introducción y el contexto del Sprint 3, la estructura, las variables de entorno y el historial de sprints.
- Estructura del Sprint 3: carpeta `reportes/` y scripts de datos en `migrations/sql/`; se elimina `migrations/sql_datos_generados/`.
- El archivo `.env` pasa a versionarse con las variables no secretas `API_URL` y `API_URL_MONEDAS`; `DATABASE_URL` queda fuera del repositorio.
- Ampliación de `.gitignore` con los reportes generados (`*.xlsx`, `*.csv`), la caché de Scrapy y los `*.log`.
- Incorporación de las dependencias `scrapy`, `pandas` y `openpyxl`.
- Corrección Sprint 1 – Ej 02: `Stock` y `Precio` referencian al objeto `Libro` en lugar de un identificador, y `Libro` conoce sus precios y su stock.
- Corrección Sprint 1 – Ej 03: `Libro` pasa a tener `id` entero y el stock se busca por `libro_id` (`leer_por_libro(libro_id: int)`).
- Corrección Sprint 2 – Ej 04: relación Libro 1 — N Precio (un precio por moneda, `UNIQUE(libro_id, moneda_id)`) y eliminación de `libros.precio_id`; se actualizan los CSV de origen.
- Corrección Sprint 2 – Ej 07: si la API informa una casa cuyo tipo de cotización no existe, el tipo se crea en lugar de fallar; `API_URL` se versiona en `.env`.
- Corrección Sprint 2 – Ej 08: la lista bimonetaria admite cualquier moneda, el usuario elige el tipo de cotización del dólar y las demás monedas se toman de la API de cotizaciones (`API_URL_MONEDAS`); el CSV de precios tiene una columna por moneda.
- Corrección Sprint 2 – Descuentos: imports solo al inicio de cada archivo y docstrings estilo Google en todos los módulos, clases y métodos.
- Los repositorios SQLAlchemy pasan a llamarse `RepositorioGenero`, `RepositorioLibro`, etc., y se eliminan los repositorios CSV.
- Nueva función `recrear_tablas()` para actualizar el esquema de una base creada en el Sprint 2.

# Sprint 2

[Ejercicio 08]
- Incorporación de las tres opciones de menú nuevas: obtener las cotizaciones por API, ver la lista de precios bimonetaria y exportar los precios a CSV.
- Reporte bimonetario con la cotización Oficial (valor de venta) para convertir precios de pesos a dólares, sin inventar valores para las monedas que no tienen cotización real.
- Exportación de los precios de todos los libros a un archivo CSV con una columna por cada moneda registrada, dentro de la carpeta `exports/`, excluida de Git.
- Pruebas automatizadas de la conversión bimonetaria y de la exportación a CSV, incluidos los casos de monedas sin cotización real (`tests/test_reportes.py`).

[Ejercicio 07]
- Obtención de las cotizaciones del dólar desde la API configurada en `API_URL`, usando `urllib` de la biblioteca estándar con un `User-Agent` propio y tiempo máximo de espera.
- Método `obtener_cotizaciones()` en `ServicioCotizacionDolar`, con la correspondencia entre las casas de la API y los tipos del sistema (`bolsa` corresponde a MEP y `contadoconliqui` a CCL).
- Registro sin duplicados: si ya existe una cotización del mismo tipo y fecha, se actualiza en lugar de insertarse nuevamente.
- Omisión de las casas desconocidas y de los registros sin valores, y resolución previa de todos los registros antes de escribir en la base.
- Pruebas automatizadas del servicio de cotizaciones con respuestas simuladas, sin acceso a la red (`tests/test_api_cotizaciones.py`).

[Ejercicio 06]
- Implementación de los repositorios sobre SQLAlchemy en `repositories.py`, implementando las mismas interfaces que los repositorios CSV.
- Conversión entre los modelos ORM y las entidades de dominio dentro de los repositorios, conservando el encapsulamiento de las entidades del Sprint 1.
- Lecturas con `obtener_sesion()` y escrituras con `transaccion()`, con confirmación y reversión automáticas.
- Integración en `main.py` y respeto del parámetro `import_default_data`: con `False` no se ejecuta ninguna precarga de datos.
- Cierre garantizado de la conexión en `main()`: el motor se libera aunque falle la migración, la construcción de los servicios o la ejecución de la consola.
- Corrección del orden de alta y de baja de libros para respetar las claves foráneas `libros.precio_id` y `stock.libro_isbn`.
- Corrección del objeto devuelto por `ServicioLibro.crear()`: se relee el libro después de persistir el stock, para que incluya el stock real con su identificador y no el stock provisorio usado para construirlo.
- Incorporación de la prueba de regresión `test_el_libro_devuelto_incluye_el_stock_persistido`, que compara los datos de stock del libro devuelto con los del recuperado desde el repositorio.
- Pruebas automatizadas de los repositorios y de los servicios operando sobre la base de datos, sobre una base SQLite en memoria (`tests/test_repositorios.py`, `tests/test_servicios.py`).

[Ejercicio 05]
- Creación de `migrations/migrations.py` con la función `migrar_datos(carpeta_csvs, carpeta_sqls)`, que lee los CSV del Sprint 1 y genera un script `.sql` de inserción por tabla.
- Separación de carpetas: los scripts de datos generados se escriben únicamente en `migrations/sql_datos_generados/`, mientras que `migrations/sql/` queda reservada para scripts de estructura; `aplicar_migracion()` rechaza las sentencias DDL para no mezclar ambas cosas.
- Scripts idempotentes mediante `ON CONFLICT DO NOTHING`, ordenados según las dependencias de claves foráneas.
- Aplicación de la migración en una única transacción, con creación previa del esquema.
- Lectura de los CSV en UTF-8 tolerante a BOM (`utf-8-sig`) y escritura de los scripts en UTF-8 sin BOM, para conservar los acentos y la ñ.
- Pruebas automatizadas de la migración: firma de la función, orden de dependencias, idempotencia, atomicidad, separación de estructura y datos, codificación y errores controlados (`tests/test_migraciones.py`).

[Ejercicio 04]
- Creación de `models/models.py` con las ocho tablas del sistema, sus tipos de datos, restricciones y relaciones.
- Claves foráneas, restricciones de unicidad (incluidas las relaciones uno a uno de libros con precios y stock) y restricciones de verificación de valores.
- Claves primarias sin autoincremento, porque los identificadores los provee la aplicación.
- Validaciones de dominio en los setters de las entidades (`Moneda`, `Precio`, `Stock` y `Libro`): texto no vacío (se rechazan también las cadenas formadas solo por espacios, sin alterar el valor almacenado), cantidades no negativas y relaciones no nulas, con `ValueError` como excepción, igual que las validaciones existentes. Acompañan a las columnas `NOT NULL` del modelo; el mínimo de stock es una validación de dominio que no se replica como restricción en la base.
- Pruebas automatizadas del esquema, de las relaciones y de las restricciones (`tests/test_modelos.py`) y de las validaciones de las entidades, incluidos los valores límite (`tests/test_entidades.py`).

[Ejercicio 03]
- Implementación del context manager de transacciones `ConexionDB.transaccion()`, con confirmación automática al salir del bloque y reversión ante errores.
- Documentación del contrato de sesiones: `obtener_sesion()` se usa para lecturas y `transaccion()` para operaciones de escritura.

[Ejercicio 02]
- Creación de la clase `ConexionDB` en `database/connection.py` para administrar el motor de SQLAlchemy, las sesiones y las transacciones.
- Normalización de la URL de conexión al driver `psycopg` (v3) para que no dependa de la versión de SQLAlchemy instalada.
- Carga de las variables de entorno con ruta explícita al archivo `.env` de la raíz del proyecto.
- Configuración del pool de conexiones con `pool_pre_ping`, reciclado de conexiones ociosas y tiempo máximo de espera.
- Verificación de conectividad mediante `probar_conexion()`.
- Configuración de la credencial de la base de datos (`DATABASE_URL`) a través de los secretos de Colab, sin escribirla en archivos ni imprimirla en las salidas del notebook.
- Pruebas automatizadas de la normalización de la URL de conexión y del contrato de sesiones y transacciones (`tests/test_conexion.py`).

[Ejercicio 01]
- Creación de la rama `Sprint_2` a partir de `Sprint_1`.
- Actualización de `README.md` con el objetivo, la introducción y el contexto del Sprint 2.
- Ampliación de `.gitignore` con `.venv/`, `exports/` y otros archivos generados por las herramientas.
- Incorporación de las dependencias `SQLAlchemy`, `psycopg[binary]` y `python-dotenv`.
- Alta de la variable no secreta `API_URL` en el archivo `.env`, que permanece excluido de Git.
- Correcciones del notebook: se completó la URL del repositorio del grupo en el comando de clonado, se agregó la celda de importación de librerías antes del Ejercicio 01, se agregó una celda de instalación de dependencias y se definió `/content/book_manager` como destino explícito del clonado, de modo que las celdas de posicionamiento encuentren el repositorio al ejecutar el notebook de principio a fin.
- Clonado del notebook protegido: la celda se ejecuta con `subprocess` y el token de GitHub se enmascara en cualquier salida, para que no quede expuesto si la operación falla.
- Corrección de seguridad en la celda de muestra del código fuente: los archivos `.env` se informan únicamente con los nombres de sus variables, sin exponer sus valores.

# Sprint 1

[Ejercicio 07]
- Creación del archivo `main.py` como punto de entrada principal.
- Configuración de la ejecución del sistema y orquestación de la aplicación.

[Ejercicio 06]
- Armado de las interfaces gráficas del sistema (consola) para operar con los CRUD de cada clase.
- Se incorporó Pydantic para validar y estructurar los datos ingresados desde la interfaz de consola.
- Se agregaron modelos de entrada en `schemas.py`.
- Se mantuvieron las entidades de dominio como clases POO con encapsulamiento mediante atributos privados y properties.
- Se integraron las validaciones de Pydantic con los servicios existentes sin alterar la lógica de negocio.
- Se realizaron pruebas de validación e integración de la consola.

[Ejercicio 05]
- Creación de archivos CSV dentro de `migrations/csv` con un mínimo de 10 registros por entidad.
- Implementación del script de importación de datos en `preload_data.py`.

[Ejercicio 04]
- Implementación de la capa de servicios para la lógica de negocio.
- Orquestación de operaciones entre las entidades y los repositorios.

[Ejercicio 03]
- Implementación de repositorios para la persistencia de datos.
- Desarrollo de métodos CRUD completos (Create, Read, Update, Delete) para cada entidad.

[Ejercicio 02]
- Definición de clases de dominio (Libro, Genero, Editorial, Precio, Stock, etc.).
- Implementación de encapsulamiento con decoradores property y type hints.

[Ejercicio 01]
- Creación de la estructura de directorios base del proyecto.
- Configuración inicial del entorno y control de versiones.
- Redacción de README.md con contexto del Sprint 1.
