from unittest.mock import MagicMock

import pytest

from app.inventory import update_product_stock


def make_mock_connection(rowcount=1):
    """Create a fake database connection for testing."""
    connection = MagicMock()
    cursor = MagicMock()
    cursor.rowcount = rowcount

    connection.cursor.return_value.__enter__.return_value = cursor

    return connection, cursor


def test_update_product_stock_executes_update_and_commits():
    connection, cursor = make_mock_connection()

    update_product_stock(connection, product_id=3, new_stock=25)

    cursor.execute.assert_called_once()
    assert "UPDATE products" in cursor.execute.call_args.args[0]
    assert cursor.execute.call_args.kwargs == {
        "new_stock": 25,
        "product_id": 3,
    }
    connection.commit.assert_called_once()


def test_update_product_stock_rejects_negative_quantity():
    connection, cursor = make_mock_connection()

    with pytest.raises(ValueError, match="non-negative whole number"):
        update_product_stock(connection, product_id=3, new_stock=-1)

    cursor.execute.assert_not_called()
    connection.commit.assert_not_called()


def test_update_product_stock_rejects_fractional_quantity():
    connection, cursor = make_mock_connection()

    with pytest.raises(ValueError, match="non-negative whole number"):
        update_product_stock(connection, product_id=3, new_stock=2.5)

    cursor.execute.assert_not_called()
    connection.commit.assert_not_called()


def test_update_product_stock_rejects_missing_product():
    connection, cursor = make_mock_connection(rowcount=0)

    with pytest.raises(ValueError, match="No product found with ID 999"):
        update_product_stock(connection, product_id=999, new_stock=10)

    connection.commit.assert_not_called()
