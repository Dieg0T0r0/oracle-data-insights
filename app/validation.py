from datetime import date


def is_valid_date_range(start_date: date, end_date: date) -> bool:
    """Return True when the start date is not after the end date."""
    return start_date <= end_date


def is_valid_stock_quantity(quantity) -> bool:
    """Return True for non-negative whole-number stock quantities."""
    return (
        isinstance(quantity, int)
        and not isinstance(quantity, bool)
        and quantity >= 0
    )
