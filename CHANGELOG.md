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
