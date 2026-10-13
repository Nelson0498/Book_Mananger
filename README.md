# Sprint 2: Book Manager con persistencia en base de datos relacional

## Objetivo

El objetivo principal de este proyecto es aplicar los conocimientos adquiridos en
programación orientada a objetos, almacenamiento de datos para su persistencia y
acceso a bases de datos relacionales mediante un ORM.

## Introducción y Contexto del problema

Una librería con venta al público necesita modernizar su sistema de gestión de
inventario de libros. Debido a la fluctuación en los costos de importación de
material bibliográfico, el sistema debe gestionar precios en diferentes monedas y
seguir de cerca la cotización del dólar para actualizar sus valores en tiempo real.

En el **Sprint 1** se desarrolló una aplicación de consola (CLI) en Python con las
entidades del dominio encapsuladas, una capa de servicios con la lógica de negocio
y repositorios que persistían en archivos CSV.

En el **Sprint 2** se amplía el alcance: la aplicación pasa a persistir en una base
de datos relacional PostgreSQL (alojada en Supabase) utilizando **SQLAlchemy** como
ORM. Los datos de los archivos CSV del Sprint 1 se migran a tablas relacionales
mediante una migración reproducible que genera los scripts `.sql` correspondientes.
Además, el sistema consulta una **API externa** para obtener las cotizaciones del
dólar y las registra en la base de datos.

## Estructura del proyecto

```
book_manager/
├── src/
│   └── book_manager/
│       ├── database/
│       │   └── connection.py       # ConexionDB: motor, sesiones y transacciones
│       ├── entities/
│       │   └── entities.py         # Entidades del dominio (Sprint 1)
│       ├── models/
│       │   └── models.py           # Tablas del sistema (ORM SQLAlchemy)
│       ├── preload_data/
│       │   └── preload_data.py     # Precarga de datos del Sprint 1
│       ├── repositories/
│       │   └── repositories.py     # Repositorios CSV (Sprint 1) y SQLAlchemy (Sprint 2)
│       ├── schemas/
│       │   └── schemas.py          # Validación de entrada con Pydantic
│       ├── services/
│       │   └── services.py         # Lógica de negocio
│       ├── migrations/
│       │   ├── csv/                # Datos de origen del Sprint 1 (solo lectura)
│       │   ├── sql/                # Scripts de estructura (DDL), reservada
│       │   ├── sql_datos_generados/  # Scripts .sql de datos generados desde los CSV
│       │   └── migrations.py       # Migración de CSV a SQL
│       ├── ui/
│       │   └── console.py          # Interfaz de consola
│       └── main.py                 # Punto de entrada
├── tests/                          # Pruebas automatizadas
├── .env                            # Variables de entorno (ignorado por Git)
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

### Migraciones: estructura y datos separados

- **Estructura:** la crean los modelos ORM con `crear_tablas()`
  (`Base.metadata.create_all()`). Si en el futuro se agregan scripts de
  estructura, van en `migrations/sql/`.
- **Datos:** `migrar_datos()` genera un script `.sql` por tabla desde los CSV y
  los escribe **únicamente** en `migrations/sql_datos_generados/`, de modo que
  nunca sobrescriba un script de estructura. `aplicar_migracion()` ejecuta esa
  carpeta y rechaza cualquier sentencia DDL.

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
raíz del proyecto. **El archivo `.env` está excluido de Git y nunca debe contener
datos versionados.**

| Variable | Descripción | ¿Secreta? |
| --- | --- | --- |
| `DATABASE_URL` | URL de conexión a PostgreSQL. | Sí |
| `API_URL` | Endpoint de la API de cotizaciones del dólar. | No |

Ejemplo de `.env` local:

```ini
DATABASE_URL=postgresql://usuario:contrasena@host:5432/postgres
API_URL=https://dolarapi.com/v1/dolares
```

El esquema `postgresql://` se normaliza automáticamente al driver `psycopg` (v3)
en `ConexionDB`, por lo que no es necesario agregar `+psycopg` a mano.

**En Google Colab** la credencial no se escribe en disco: `DATABASE_URL` se obtiene
desde los *Secrets* del notebook y se expone como variable de entorno, mientras que
`API_URL` permanece en el archivo `.env` por no ser un dato sensible.

```python
import os
from google.colab import userdata

os.environ["DATABASE_URL"] = userdata.get("DATABASE_URL")
```

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

### Parámetro `import_default_data`

| Valor | Comportamiento |
| --- | --- |
| `True` (por defecto) | Asegura el esquema y ejecuta la migración de los CSV a la base de datos. |
| `False` | No ejecuta ninguna precarga: omite por completo la importación de datos. |

## Reglas de negocio

- **Conversión de precios a dólares:** el reporte bimonetario convierte los precios
  expresados en pesos (ARS) a dólares (USD) utilizando la **cotización Oficial,
  valor de venta** vigente. Es la única conversión que se calcula.
- **Monedas sin cotización real:** no se inventan valores de cambio. Las monedas
  distintas de ARS y USD se muestran únicamente cuando el precio ya está expresado
  en ellas, y se informan como no disponibles en caso contrario.
- **Cotizaciones duplicadas:** la API del dólar se registra una vez por tipo y fecha
  (restricción de unicidad en la base de datos); volver a consultarla actualiza los
  valores existentes en lugar de duplicar registros.

## Pruebas automatizadas

Las pruebas utilizan `unittest` de la biblioteca estándar y una base SQLite en
memoria, por lo que **no requieren conexión a PostgreSQL ni credenciales**:

```bash
$env:PYTHONPATH = "src"        # En Linux o macOS: export PYTHONPATH=src
python -m unittest discover -s tests -t . -v
```

Cubren la normalización de la URL de conexión, el contrato de sesiones y
transacciones, el esquema y sus restricciones, la migración de CSV a SQL, los
repositorios, los servicios y los reportes (con la API simulada, sin red).

## Historial de sprints

| Sprint | Alcance | Persistencia |
| --- | --- | --- |
| 1 | Entidades, servicios, consola y CRUD completo. | Archivos CSV |
| 2 | Modelos ORM, migración de datos, API del dólar y reportes. | PostgreSQL (Supabase) vía SQLAlchemy |
