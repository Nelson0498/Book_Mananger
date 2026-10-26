-- Migración de libros.csv a la tabla libros.
-- Script generado automáticamente por migrations.py.
-- ON CONFLICT DO NOTHING evita duplicar registros.
INSERT INTO libros (id, isbn, titulo, autor, editorial_id, genero_id) VALUES
    (1, '978-950-731-001-1', 'Cien años de soledad', 'Gabriel García Márquez', 1, 1),
    (2, '978-950-731-002-8', 'El túnel', 'Ernesto Sabato', 4, 1),
    (3, '978-84-204-8311-5', 'Fahrenheit 451', 'Ray Bradbury', 2, 3),
    (4, '978-987-566-847-3', 'El Aleph', 'Jorge Luis Borges', 5, 6),
    (5, '978-84-339-7082-9', '1984', 'George Orwell', 6, 3),
    (6, '978-950-49-0001-2', 'Martín Fierro', 'José Hernández', 3, 9),
    (7, '978-84-7223-084-0', 'Drácula', 'Bram Stoker', 10, 4),
    (8, '978-987-1210-01-6', 'Historia económica de la Argentina', 'Aldo Ferrer', 9, 7),
    (9, '978-84-9838-133-5', 'Orgullo y prejuicio', 'Jane Austen', 7, 5),
    (10, '978-987-04-0156-3', 'Rayuela', 'Julio Cortázar', 5, 1)
ON CONFLICT DO NOTHING;
