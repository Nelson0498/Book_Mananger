# Scripts de datos generados

Los archivos `.sql` de esta carpeta los genera automáticamente
`migrar_datos()` a partir de los CSV de `../csv/`, un script por tabla y en el
orden que respetan las claves foráneas.

**No se editan a mano:** cualquier cambio se pierde en la próxima generación.
Para modificarlos hay que cambiar los CSV de origen o el código de
`../migrations.py`.

Son idempotentes (`ON CONFLICT DO NOTHING`), por lo que pueden aplicarse más de
una vez sin duplicar registros. Se aplican con `aplicar_migracion()`.
