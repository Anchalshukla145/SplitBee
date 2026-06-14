"""
Currency conversion module.
Handles exchange rates for the Priya scenario.
Base currency: INR.
"""
from database.db import fetch_one, fetch_all, execute

# Symbols for display
CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "AUD": "A$",
    "CAD": "C$",
}

BASE_CURRENCY = "INR"


def get_symbol(code):
    """Return the currency symbol for a code."""
    return CURRENCY_SYMBOLS.get(code, code)


def format_currency(amount, code="INR"):
    """Format like ₹1,234.56"""
    symbol = get_symbol(code)
    if code == "JPY":
        return f"{symbol}{amount:,.0f}"
    return f"{symbol}{amount:,.2f}"


def get_exchange_rate(from_currency, to_currency):
    """
    Get exchange rate from DB.
    Returns rate (float) or None.
    """
    if from_currency == to_currency:
        return 1.0

    row = fetch_one(
        "SELECT rate FROM exchange_rates WHERE from_currency = ? AND to_currency = ?",
        (from_currency, to_currency)
    )
    if row:
        return row["rate"]

    # Try reverse
    row = fetch_one(
        "SELECT rate FROM exchange_rates WHERE from_currency = ? AND to_currency = ?",
        (to_currency, from_currency)
    )
    if row and row["rate"] != 0:
        return round(1.0 / row["rate"], 4)

    return None


def convert_currency(amount, from_currency, to_currency="INR"):
    """
    Convert an amount between currencies.
    Returns converted amount or None if rate not found.
    """
    rate = get_exchange_rate(from_currency, to_currency)
    if rate is None:
        return None
    return round(amount * rate, 2)


def normalize_to_base(amount, currency):
    """Convert any amount to base currency (INR)."""
    return convert_currency(amount, currency, BASE_CURRENCY)


def get_all_rates():
    """Return all exchange rates."""
    return fetch_all("SELECT * FROM exchange_rates ORDER BY from_currency")


def update_rate(from_currency, to_currency, rate):
    """Update or insert an exchange rate."""
    existing = fetch_one(
        "SELECT id FROM exchange_rates WHERE from_currency = ? AND to_currency = ?",
        (from_currency, to_currency)
    )
    if existing:
        execute(
            "UPDATE exchange_rates SET rate = ?, updated_at = datetime('now') WHERE id = ?",
            (rate, existing["id"])
        )
    else:
        execute(
            "INSERT INTO exchange_rates (from_currency, to_currency, rate) VALUES (?, ?, ?)",
            (from_currency, to_currency, rate)
        )


def currency_options():
    """Return list of 'CODE (symbol)' for dropdowns."""
    return [f"{code} ({sym})" for code, sym in CURRENCY_SYMBOLS.items()]


def parse_currency_option(option_str):
    """Extract code from 'CODE (symbol)' string."""
    return option_str.split(" ")[0]
