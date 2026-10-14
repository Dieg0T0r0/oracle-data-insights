from pathlib import Path

import oracledb
from dotenv import load_dotenv
import os

load_dotenv()

sql_file = Path("sql/02_create_tables.sql")
sql_text = sql_file.read_text(encoding="utf-8")

# Remove full-line SQL comments, then split statements by semicolon.
lines = [
    line for line in sql_text.splitlines()
    if not line.strip().startswith("--")
]
statements = [
    statement.strip()
    for statement in "\n".join(lines).split(";")
    if statement.strip()
]

with oracledb.connect(
    user=os.environ["ORACLE_USER"],
    password=os.environ["ORACLE_PASSWORD"],
    dsn=os.environ["ORACLE_DSN"],
    config_dir=os.environ["ORACLE_WALLET_LOCATION"],
    wallet_location=os.environ["ORACLE_WALLET_LOCATION"],
    wallet_password=os.environ["ORACLE_WALLET_PASSWORD"],
) as connection:
    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
            print("Created:", statement.split()[2])

        cursor.execute("""
            SELECT table_name
            FROM user_tables
            WHERE table_name IN (
                'CUSTOMERS', 'PRODUCTS', 'ORDERS', 'ORDER_ITEMS'
            )
            ORDER BY table_name
        """)

        print("\nTables in Autonomous Database:")
        for (table_name,) in cursor.fetchall():
            print("-", table_name)

print("\nSchema creation complete.")
