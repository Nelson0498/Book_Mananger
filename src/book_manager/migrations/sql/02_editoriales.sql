-- Migración de editoriales.csv a la tabla editoriales.
-- Script generado automáticamente por migrations.py.
-- ON CONFLICT DO NOTHING evita duplicar registros.
INSERT INTO editoriales (id, nombre, pais) VALUES
    (1, 'Planeta', 'Argentina'),
    (2, 'Penguin Random House', 'España'),
    (3, 'Alfaguara', 'España'),
    (4, 'Emecé', 'Argentina'),
    (5, 'Sudamericana', 'Argentina'),
    (6, 'Anagrama', 'España'),
    (7, 'Tusquets', 'España'),
    (8, 'Siglo XXI', 'México'),
    (9, 'Fondo de Cultura Económica', 'México'),
    (10, 'Salamandra', 'España')
ON CONFLICT DO NOTHING;
