# Scripts de estructura (DDL)

Esta carpeta está reservada para los scripts `.sql` que definen **estructura**
(`CREATE TABLE`, `ALTER TABLE`, índices, etc.).

Los scripts de **inserción de datos** que `migrar_datos()` genera a partir de
los CSV **no se escriben acá**: van a `../sql_datos_generados/`. Así la
migración de datos no puede sobrescribir un script de estructura.

Hoy la estructura la crea SQLAlchemy desde los modelos declarados en
`src/book_manager/models/models.py`, mediante `crear_tablas()`
(`Base.metadata.create_all()`), por lo que esta carpeta puede quedar vacía.

Si en el futuro se agregan scripts de estructura, deben aplicarse con un
mecanismo propio: `aplicar_migracion()` rechaza las sentencias DDL para no
mezclar estructura con datos.
