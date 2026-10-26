-- Migración de precios.csv a la tabla precios.
-- Script generado automáticamente por migrations.py.
-- ON CONFLICT DO NOTHING evita duplicar registros.
INSERT INTO precios (id, libro_id, moneda_id, valor) VALUES
    (1, 1, 1, 15000.0),
    (2, 2, 1, 12500.0),
    (3, 3, 2, 29.99),
    (4, 4, 1, 18900.0),
    (5, 5, 2, 35.5),
    (6, 6, 1, 9800.0),
    (7, 7, 2, 22.0),
    (8, 8, 1, 14200.0),
    (9, 9, 2, 19.99),
    (10, 10, 1, 11500.0),
    (11, 1, 2, 10.0),
    (12, 2, 2, 8.33),
    (13, 3, 1, 44985.0),
    (14, 4, 2, 12.6),
    (15, 5, 1, 53250.0),
    (16, 6, 2, 6.53),
    (17, 7, 1, 33000.0),
    (18, 8, 2, 9.47),
    (19, 9, 1, 29985.0),
    (20, 10, 2, 7.67)
ON CONFLICT DO NOTHING;
