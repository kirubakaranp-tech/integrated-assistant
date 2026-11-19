DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
    id             INTEGER PRIMARY KEY,
    customer_id    INTEGER NOT NULL,
    status         TEXT NOT NULL
                   CHECK (status IN ('processing', 'shipped', 'out_for_delivery', 'delivered', 'cancelled')),
    order_date     DATE NOT NULL,
    shipped_date   DATE,
    delivered_date DATE,
    total_amount   NUMERIC(10, 2) NOT NULL
);

CREATE TABLE order_items (
    id           SERIAL PRIMARY KEY,
    order_id     INTEGER NOT NULL REFERENCES orders(id),
    product_name TEXT NOT NULL,
    quantity     INTEGER NOT NULL,
    unit_price   NUMERIC(10, 2) NOT NULL
);

INSERT INTO orders (id, customer_id, status, order_date, shipped_date, delivered_date, total_amount) VALUES
(1031, 1, 'delivered',        '2026-02-02', '2026-02-04', '2026-02-07', 2499.00),
(1032, 2, 'delivered',        '2026-02-05', '2026-02-06', '2026-02-09',  799.00),
(1033, 3, 'delivered',        '2026-02-10', '2026-02-11', '2026-02-14', 1598.00),
(1034, 4, 'cancelled',        '2026-02-12', NULL,         NULL,         3499.00),
(1035, 5, 'delivered',        '2026-02-15', '2026-02-17', '2026-02-20',  449.00),
(1036, 1, 'delivered',        '2026-02-20', '2026-02-21', '2026-02-24', 1299.00),
(1037, 2, 'delivered',        '2026-02-25', '2026-02-26', '2026-03-01', 5999.00),
(1038, 3, 'delivered',        '2026-03-01', '2026-03-03', '2026-03-06',  999.00),
(1039, 4, 'delivered',        '2026-03-03', '2026-03-04', '2026-03-07', 1898.00),
(1040, 5, 'cancelled',        '2026-03-05', NULL,         NULL,          699.00),
(1041, 1, 'delivered',        '2026-03-07', '2026-03-09', '2026-03-12', 2199.00),
(1042, 3, 'out_for_delivery', '2026-03-10', '2026-03-12', NULL,         3297.00),
(1043, 2, 'out_for_delivery', '2026-03-11', '2026-03-13', NULL,          899.00),
(1044, 4, 'shipped',          '2026-03-12', '2026-03-14', NULL,         1499.00),
(1045, 5, 'shipped',          '2026-03-13', '2026-03-14', NULL,         2598.00),
(1046, 1, 'shipped',          '2026-03-14', '2026-03-15', NULL,          349.00),
(1047, 3, 'processing',       '2026-03-15', NULL,         NULL,         4999.00),
(1048, 2, 'processing',       '2026-03-15', NULL,         NULL,         1199.00),
(1049, 4, 'processing',       '2026-03-16', NULL,         NULL,          599.00),
(1050, 5, 'processing',       '2026-03-16', NULL,         NULL,         1749.00);

INSERT INTO order_items (order_id, product_name, quantity, unit_price) VALUES
(1031, 'Wireless Headphones', 1, 2499.00),
(1032, 'Phone Case', 1, 799.00),
(1033, 'USB-C Cable', 2, 299.00),
(1033, 'Power Bank', 1, 1000.00),
(1034, 'Smart Watch', 1, 3499.00),
(1035, 'Screen Guard', 1, 449.00),
(1036, 'Bluetooth Speaker', 1, 1299.00),
(1037, 'Mechanical Keyboard', 1, 5999.00),
(1038, 'Wireless Mouse', 1, 999.00),
(1039, 'Laptop Stand', 1, 1499.00),
(1039, 'Mouse Pad', 1, 399.00),
(1040, 'Phone Charger', 1, 699.00),
(1041, 'Webcam', 1, 2199.00),
(1042, 'Wireless Earbuds', 1, 2499.00),
(1042, 'USB-C Charger', 1, 798.00),
(1043, 'Fitness Band', 1, 899.00),
(1044, 'Portable SSD', 1, 1499.00),
(1045, 'Desk Lamp', 2, 1299.00),
(1046, 'Cable Organizer', 1, 349.00),
(1047, 'Noise Cancelling Headphones', 1, 4999.00),
(1048, 'HDMI Cable', 1, 1199.00),
(1049, 'Phone Holder', 1, 599.00),
(1050, 'Keyboard Cover', 1, 349.00),
(1050, 'Gaming Mouse', 1, 1400.00);
