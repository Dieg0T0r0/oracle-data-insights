import os
from pathlib import Path

import oracledb
from dotenv import load_dotenv

load_dotenv()

sql_text = Path("sql/03_insert_sample_data.sql").read_text(
    encoding="utf-8"
)

# Split the four INSERT ALL statements at their final semicolons.
statements = [
    statement.strip()
    for statement in sql_text.split(";")
    if statement.strip()
    and not all(
        line.strip().startswith("--")
        for line in statement.splitlines()
        if line.strip()
    )
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
            # Strip leading comments before executing.
            cleaned = "\n".join(
                line for line in statement.splitlines()
                if not line.strip().startswith("--")
            ).strip()
            if cleaned:
                cursor.execute(cleaned)

        for table in ("CUSTOMERS", "PRODUCTS", "ORDERS", "ORDER_ITEMS"):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"{table}: {cursor.fetchone()[0]}")

    connection.commit()

print("Sample data loaded.")
