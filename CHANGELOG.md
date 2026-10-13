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
