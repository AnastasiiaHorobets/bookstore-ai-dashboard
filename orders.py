from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

EXCHANGE_RATES = {
    "USD": Decimal(1),
    "EUR": Decimal("1.2"),
}


def normalize_price_text(prices):
    return prices.astype("string").str.strip().str.upper()


def extract_currency(price_text):
    currency = price_text.str.extract(r"(USD|EUR|\$|€)", expand=False)
    return currency.replace({"$": "USD", "€": "EUR"})


def extract_amount(price_text):
    return (
        price_text.str.replace(r"^(\d+)\s*[$€]\s*(\d{2})¢$", r"\1.\2", regex=True)
        .str.replace(r"USD|EUR|\$|€", "", regex=True)
        .str.strip()
        .str.replace(r"^(\d+)¢(\d{2})$", r"\1.\2", regex=True)
        .str.replace(r"^(\d+)\.$", r"\1", regex=True)
    )


def validate_prices(currency, amount):
    valid = amount.str.fullmatch(r"\d+(?:\.\d{1,2})?", na=False)
    if currency.isna().any() or not valid.all():
        raise ValueError("Some prices could not be parsed")


def clean_prices(orders_df):
    orders = orders_df.copy()
    price_text = normalize_price_text(orders["unit_price"])
    currency = extract_currency(price_text)
    amount = extract_amount(price_text)
    validate_prices(currency, amount)

    orders["currency"] = currency
    orders["amount"] = amount
    return orders


def calculate_order_total(amount, quantity, currency):
    total = Decimal(amount) * int(quantity) * EXCHANGE_RATES[currency]
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_paid_price(orders_df):
    orders = orders_df.copy()
    orders["paid_price"] = [
        calculate_order_total(amount, quantity, currency)
        for amount, quantity, currency in zip(
            orders["amount"], orders["quantity"], orders["currency"]
        )
    ]
    return orders


def normalize_timestamp_text(timestamps):
    return (
        timestamps.astype("string")
        .str.strip()
        .str.replace(r"(?i)A\.M\.", "AM", regex=True)
        .str.replace(r"(?i)P\.M\.", "PM", regex=True)
        .str.replace(r"[;,]", " ", regex=True)
        .str.replace(r"\s+", " ", regex=True)
    )


def clean_timestamps(orders_df):
    orders = orders_df.copy()
    text = normalize_timestamp_text(orders["timestamp"])
    orders["timestamp"] = pd.to_datetime(text, format="mixed", errors="coerce")
    orders["date"] = orders["timestamp"].dt.date
    return orders


def validate_orders(orders_df):
    print("Duplicate order IDs:", orders_df["id"].duplicated().sum())
    print("Non-positive quantities:", orders_df["quantity"].le(0).sum())
    print("Missing timestamps:", orders_df["timestamp"].isna().sum())
