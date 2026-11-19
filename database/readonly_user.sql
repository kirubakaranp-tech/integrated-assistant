GRANT USAGE ON SCHEMA public TO assistant_readonly;
GRANT SELECT ON orders, order_items TO assistant_readonly;

ALTER ROLE assistant_readonly SET default_transaction_read_only = on;
