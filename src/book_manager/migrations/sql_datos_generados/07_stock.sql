-- Migración de stock.csv a la tabla stock.
-- Script generado automáticamente por migrations.py.
-- ON CONFLICT DO NOTHING evita duplicar registros.
INSERT INTO stock (id_stock, libro_isbn, cantidad, cantidad_minima) VALUES
    (1, '978-950-731-001-1', 25, 5),
    (2, '978-950-731-002-8', 18, 3),
    (3, '978-84-204-8311-5', 12, 2),
    (4, '978-987-566-847-3', 30, 5),
    (5, '978-84-339-7082-9', 8, 3),
    (6, '978-950-49-0001-2', 40, 10),
    (7, '978-84-7223-084-0', 15, 4),
    (8, '978-987-1210-01-6', 6, 2),
    (9, '978-84-9838-133-5', 22, 5),
    (10, '978-987-04-0156-3', 35, 8)
ON CONFLICT DO NOTHING;
