import os
from pathlib import Path

import oracledb
import pandas as pd
import streamlit as st
import logging

from dotenv import load_dotenv
from app.logging_config import configure_logging
from app.inventory import update_product_stock
from app.validation import is_valid_date_range

# Load configuration from the project root.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
logger = configure_logging()

st.set_page_config(
    page_title="Oracle Data Insights",
    page_icon="📊",
    layout="wide",
)

st.title("Oracle Data Insights")
st.caption("Sales, customer, and inventory analytics powered by Oracle Database")


st.sidebar.header("Dashboard Filters")

status_options = [
    "All",
    "DELIVERED",
    "SHIPPED",
    "PROCESSING",
    "PENDING",
    "CANCELLED",
]

selected_status = st.sidebar.selectbox(
    "Order status",
    status_options,
)

start_date = st.sidebar.date_input(
    "Start date",
    value=pd.Timestamp("2026-01-01").date(),
)

end_date = st.sidebar.date_input(
    "End date",
    value=pd.Timestamp.today().date(),
)

if not is_valid_date_range(start_date, end_date):
    st.sidebar.error("Start date must be before or equal to end date.")
    st.stop()


@st.cache_resource
def get_connection_pool():
    return oracledb.create_pool(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
        config_dir=os.environ["ORACLE_WALLET_LOCATION"],
        wallet_location=os.environ["ORACLE_WALLET_LOCATION"],
        wallet_password=os.environ["ORACLE_WALLET_PASSWORD"],
        min=1,
        max=3,
        increment=1,
    )

def read_query(sql, params=None):
    with get_connection_pool().acquire() as connection:
        return pd.read_sql(sql, connection, params=params)


try:

# KPI data, filtered by order status and date.
    where_parts = [
        "o.order_date >= :start_date",
        "o.order_date < :end_date + 1",
    ]
    params = {
        "start_date": start_date,
        "end_date": end_date,
    }

    if selected_status != "All":
        where_parts.append("o.status = :status")
        params["status"] = selected_status

    where_clause = " AND ".join(where_parts)

    kpis_sql = f"""
        SELECT
            (
                SELECT NVL(SUM(oi.quantity * oi.unit_price), 0)
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.order_id
                WHERE {where_clause}
            ) AS total_revenue,
            (
                SELECT COUNT(*)
                FROM orders o
                WHERE {where_clause}
            ) AS total_orders,
            (SELECT COUNT(*) FROM customers) AS total_customers,
            (
                SELECT COUNT(*)
                FROM products
                WHERE stock_quantity <= 5
            ) AS low_stock_products
        FROM dual
    """

    with get_connection_pool().acquire() as connection:
        kpis = pd.read_sql(kpis_sql, connection, params=params)

    values = kpis.iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Revenue (selected orders)", f"${values['TOTAL_REVENUE']:,.2f}")
    col2.metric("Selected Orders", f"{int(values['TOTAL_ORDERS'])}")
    col3.metric("Total Customers", f"{int(values['TOTAL_CUSTOMERS'])}")
    col4.metric("Low-Stock Products", f"{int(values['LOW_STOCK_PRODUCTS'])}")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Monthly Revenue")

        monthly = read_query(f"""
            SELECT
                TRUNC(o.order_date, 'MM') AS sales_month,
                SUM(oi.quantity * oi.unit_price) AS monthly_revenue
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE {where_clause}
            GROUP BY TRUNC(o.order_date, 'MM')
            ORDER BY sales_month
        """, params=params)


        if not monthly.empty:
            monthly["SALES_MONTH"] = pd.to_datetime(monthly["SALES_MONTH"])
            monthly = monthly.set_index("SALES_MONTH")
            st.bar_chart(monthly["MONTHLY_REVENUE"])
        else:
            st.info("No delivered sales data is available.")

    with right:
        st.subheader("Top-Selling Products")

        top_products = read_query(f"""
            SELECT
                p.product_name,
                SUM(oi.quantity) AS units_sold,
                SUM(oi.quantity * oi.unit_price) AS sales_value
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE {where_clause}
            GROUP BY p.product_id, p.product_name
            ORDER BY units_sold DESC, p.product_name
        """, params=params)

        st.dataframe(top_products, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Inventory Overview")

    inventory = read_query("""
        SELECT
            product_name,
            category,
            unit_price,
            stock_quantity,
            CASE
                WHEN stock_quantity <= 5 THEN 'Restock'
                ELSE 'In Stock'
            END AS stock_status
        FROM products
        ORDER BY stock_quantity ASC, product_name
    """)

    st.dataframe(inventory, use_container_width=True, hide_index=True)

    st.subheader("Products Requiring Restock")
    low_stock = inventory[inventory["STOCK_QUANTITY"] <= 5]
    st.dataframe(low_stock, use_container_width=True, hide_index=True)

    
    st.divider()

    st.subheader("Update Product Inventory")
    st.caption("Change a product's stock quantity and save it to Oracle Database.")

    products = read_query("""
        SELECT product_id, product_name, stock_quantity
        FROM products
        ORDER BY product_name
    """)

    with st.form("inventory_update_form"):
        selected_product = st.selectbox(
            "Select product",
            products["PRODUCT_ID"].tolist(),
            format_func=lambda product_id: (
                products.loc[
                    products["PRODUCT_ID"] == product_id,
                    "PRODUCT_NAME"
                ].iloc[0]
            ),
        )

        current_stock = int(
            products.loc[
                products["PRODUCT_ID"] == selected_product,
                "STOCK_QUANTITY"
            ].iloc[0]
        )

        st.write(f"Current stock quantity: **{current_stock}**")

        new_stock = st.number_input(
            "New stock quantity",
            min_value=0,
            max_value=100000,
            value=current_stock,
            step=1,
        )

        submitted = st.form_submit_button("Save Inventory Update")



    if submitted:
        try:
            with get_connection_pool().acquire() as connection:
                update_product_stock(
                    connection,
                    product_id=int(selected_product),
                    new_stock=int(new_stock),
                )

            st.success("Inventory updated successfully!")
            st.cache_data.clear()
            st.rerun()

        except ValueError as error:
            st.error(str(error))

    st.caption("Data is retrieved live from Oracle Autonomous Database.")

except Exception as error:
    logger.exception("Dashboard failed to load or process data.")
    st.error("The dashboard could not load data from Oracle.")
    st.caption("Check your database connection and application settings.")
    with st.expander("Technical details"):
        st.code(str(error))

