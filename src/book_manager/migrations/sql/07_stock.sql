-- Migración de stock.csv a la tabla stock.
-- Script generado automáticamente por migrations.py.
-- ON CONFLICT DO NOTHING evita duplicar registros.
INSERT INTO stock (id_stock, libro_id, cantidad, cantidad_minima) VALUES
    (1, 1, 25, 5),
    (2, 2, 18, 3),
    (3, 3, 12, 2),
    (4, 4, 30, 5),
    (5, 5, 8, 3),
    (6, 6, 40, 10),
    (7, 7, 15, 4),
    (8, 8, 6, 2),
    (9, 9, 22, 5),
    (10, 10, 35, 8)
ON CONFLICT DO NOTHING;
