-- Migración de generos.csv a la tabla generos.
-- Script generado automáticamente por migrations.py.
-- ON CONFLICT DO NOTHING evita duplicar registros.
INSERT INTO generos (id, nombre) VALUES
    (1, 'Ficción'),
    (2, 'No Ficción'),
    (3, 'Ciencia Ficción'),
    (4, 'Terror'),
    (5, 'Romance'),
    (6, 'Fantasía'),
    (7, 'Historia'),
    (8, 'Biografía'),
    (9, 'Poesía'),
    (10, 'Aventura')
ON CONFLICT DO NOTHING;
