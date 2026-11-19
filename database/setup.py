import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo

load_dotenv()

DATABASE_NAME = "orders_db"
SQL_FOLDER = Path(__file__).parent


def main():
    admin_url = os.getenv("DATABASE_ADMIN_URL")
    if not admin_url:
        print("Please set DATABASE_ADMIN_URL in your .env file first.")
        return

    with psycopg.connect(admin_url, autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DATABASE_NAME,)).fetchone()
        if not exists:
            conn.execute(f"CREATE DATABASE {DATABASE_NAME}")
            print(f"Created database {DATABASE_NAME}")

    with psycopg.connect(make_conninfo(admin_url, dbname=DATABASE_NAME), autocommit=True) as conn:
        for file_name in ["schema.sql", "readonly_user.sql"]:
            conn.execute((SQL_FOLDER / file_name).read_text())
            print(f"Ran {file_name}")

        count = conn.execute("SELECT count(*) FROM orders").fetchone()[0]
        print(f"Done: {count} orders in {DATABASE_NAME}")


if __name__ == "__main__":
    main()
