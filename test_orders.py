from decimal import Decimal

import pandas as pd

from orders import calculate_paid_price, clean_prices


def test_usd_price():
    orders = pd.DataFrame(
        {
            "unit_price": ["$ 35"],
            "quantity": [2],
        }
    )

    result = calculate_paid_price(clean_prices(orders))
    assert result["paid_price"].iloc[0] == Decimal("70.00")
