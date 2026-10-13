-- Migración de precios.csv a la tabla precios.
-- Script generado automáticamente por migrations.py.
-- ON CONFLICT DO NOTHING evita duplicar registros.
INSERT INTO precios (id, valor, moneda_id) VALUES
    (1, 15000.0, 1),
    (2, 12500.0, 1),
    (3, 29.99, 2),
    (4, 18900.0, 1),
    (5, 35.5, 2),
    (6, 9800.0, 1),
    (7, 22.0, 2),
    (8, 14200.0, 1),
    (9, 19.99, 2),
    (10, 11500.0, 1)
ON CONFLICT DO NOTHING;
