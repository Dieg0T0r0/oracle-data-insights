
from datetime import date

from app.validation import is_valid_date_range, is_valid_stock_quantity


def test_valid_date_range():
    assert is_valid_date_range(date(2026, 6, 1), date(2026, 6, 30))


def test_same_start_and_end_date():
    assert is_valid_date_range(date(2026, 6, 1), date(2026, 6, 1))


def test_invalid_date_range():
    assert not is_valid_date_range(date(2026, 7, 1), date(2026, 6, 30))


def test_valid_stock_quantity():
    assert is_valid_stock_quantity(10)


def test_zero_stock_is_valid():
    assert is_valid_stock_quantity(0)


def test_negative_stock_is_invalid():
    assert not is_valid_stock_quantity(-1)


def test_fractional_stock_is_invalid():
    assert not is_valid_stock_quantity(2.5)


def test_boolean_stock_is_invalid():
    assert not is_valid_stock_quantity(True)


def test_stock_quantity_rejects_numeric_string():
    assert not is_valid_stock_quantity("10")


def test_stock_quantity_rejects_none():
    assert not is_valid_stock_quantity(None)


def test_stock_quantity_rejects_negative_large_value():
    assert not is_valid_stock_quantity(-100)


def test_date_range_accepts_python_date_objects():
    start = date(2026, 1, 1)
    end = date(2026, 12, 31)

    assert is_valid_date_range(start, end)
