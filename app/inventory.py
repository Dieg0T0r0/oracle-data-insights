def update_product_stock(connection, product_id: int, new_stock: int) -> None:
    """Update a product's stock quantity and commit the transaction."""
    from app.validation import is_valid_stock_quantity

    if not is_valid_stock_quantity(new_stock):
        raise ValueError("Stock quantity must be a non-negative whole number.")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE products
            SET stock_quantity = :new_stock
            WHERE product_id = :product_id
            """,
            new_stock=new_stock,
            product_id=product_id,
        )

        if cursor.rowcount == 0:
            raise ValueError(f"No product found with ID {product_id}.")

    connection.commit()
