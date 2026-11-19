DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'assistant_readonly') THEN
        CREATE ROLE assistant_readonly LOGIN PASSWORD 'assistant123';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO assistant_readonly;
GRANT SELECT ON orders, order_items TO assistant_readonly;

ALTER ROLE assistant_readonly SET default_transaction_read_only = on;
