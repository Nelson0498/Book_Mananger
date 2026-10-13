-- Migración de tipos_cotizacion.csv a la tabla tipos_cotizacion.
-- Script generado automáticamente por migrations.py.
-- ON CONFLICT DO NOTHING evita duplicar registros.
INSERT INTO tipos_cotizacion (id, nombre) VALUES
    (1, 'Oficial'),
    (2, 'Blue'),
    (3, 'MEP'),
    (4, 'CCL'),
    (5, 'Tarjeta'),
    (6, 'Mayorista'),
    (7, 'Cripto'),
    (8, 'Turista'),
    (9, 'Solidario'),
    (10, 'Libre')
ON CONFLICT DO NOTHING;
