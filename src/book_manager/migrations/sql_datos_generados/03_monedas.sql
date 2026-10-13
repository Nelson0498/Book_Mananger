-- Migración de monedas.csv a la tabla monedas.
-- Script generado automáticamente por migrations.py.
-- ON CONFLICT DO NOTHING evita duplicar registros.
INSERT INTO monedas (id, codigo, nombre, simbolo) VALUES
    (1, 'ARS', 'Peso Argentino', '$'),
    (2, 'USD', 'Dólar Estadounidense', 'US$'),
    (3, 'EUR', 'Euro', '€'),
    (4, 'GBP', 'Libra Esterlina', '£'),
    (5, 'BRL', 'Real Brasileño', 'R$'),
    (6, 'CLP', 'Peso Chileno', 'CL$'),
    (7, 'UYU', 'Peso Uruguayo', '$U'),
    (8, 'MXN', 'Peso Mexicano', 'MX$'),
    (9, 'JPY', 'Yen Japonés', '¥'),
    (10, 'CAD', 'Dólar Canadiense', 'C$')
ON CONFLICT DO NOTHING;
