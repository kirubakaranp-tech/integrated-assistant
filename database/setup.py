import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

load_dotenv()

DATABASE_NAME = "orders_db"
READONLY_USER = "assistant_readonly"
SQL_FOLDER = Path(__file__).parent


def create_readonly_user(conn, password):
    exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (READONLY_USER,)).fetchone()
    command = "ALTER ROLE {} LOGIN PASSWORD {}" if exists else "CREATE ROLE {} LOGIN PASSWORD {}"
    conn.execute(sql.SQL(command).format(sql.Identifier(READONLY_USER), sql.Literal(password)))
    print(f"{'Updated' if exists else 'Created'} user {READONLY_USER}")


def main():
    admin_url = os.getenv("DATABASE_ADMIN_URL")
    app_url = os.getenv("DATABASE_URL")
    if not admin_url or not app_url:
        print("Please set DATABASE_ADMIN_URL and DATABASE_URL in your .env file first.")
        return

    password = conninfo_to_dict(app_url).get("password")
    if not password or password == "CHOOSE_A_PASSWORD":
        print("Please choose a password for the read-only user in DATABASE_URL in your .env file.")
        return

    with psycopg.connect(admin_url, autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DATABASE_NAME,)).fetchone()
        if not exists:
            conn.execute(f"CREATE DATABASE {DATABASE_NAME}")
            print(f"Created database {DATABASE_NAME}")

    with psycopg.connect(make_conninfo(admin_url, dbname=DATABASE_NAME), autocommit=True) as conn:
        conn.execute((SQL_FOLDER / "schema.sql").read_text())
        print("Ran schema.sql")

        create_readonly_user(conn, password)
        conn.execute((SQL_FOLDER / "readonly_user.sql").read_text())
        print("Ran readonly_user.sql")

        count = conn.execute("SELECT count(*) FROM orders").fetchone()[0]
        print(f"Done: {count} orders in {DATABASE_NAME}")


if __name__ == "__main__":
    main()
