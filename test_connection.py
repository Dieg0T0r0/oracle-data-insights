import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("ORACLE_USER")
password = os.getenv("ORACLE_PASSWORD")
dsn = os.getenv("ORACLE_DSN")
wallet_location = os.getenv("ORACLE_WALLET_LOCATION")
wallet_password = os.getenv("ORACLE_WALLET_PASSWORD")

required_settings = {
    "ORACLE_USER": user,
    "ORACLE_PASSWORD": password,
    "ORACLE_DSN": dsn,
    "ORACLE_WALLET_LOCATION": wallet_location,
    "ORACLE_WALLET_PASSWORD": wallet_password,
}

missing = [name for name, value in required_settings.items() if not value]
if missing:
    raise ValueError(
        "Missing .env settings: " + ", ".join(missing)
    )

try:
    with oracledb.connect(
        user=user,
        password=password,
        dsn=dsn,
        config_dir=wallet_location,
        wallet_location=wallet_location,
        wallet_password=wallet_password,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT USER FROM dual")
            current_user = cursor.fetchone()[0]

            print("Oracle connection successful!")
            print(f"Connected user: {current_user}")

            cursor.execute("""
                SELECT table_name
                FROM user_tables
                WHERE table_name IN (
                    'CUSTOMERS',
                    'PRODUCTS',
                    'ORDERS',
                    'ORDER_ITEMS'
                )
                ORDER BY table_name
            """)

            tables = [row[0] for row in cursor.fetchall()]
            print("Project tables found:", tables)

except oracledb.Error:
    print("Oracle connection failed.")
    print("Check your .env settings, wallet path, passwords,")
    print("connection alias, and network access configuration.")
    raise
