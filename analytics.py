from books import make_author_set


def count_author_sets(books_df):
    author_sets = books_df["author"].map(make_author_set)
    return author_sets.nunique()


def daily_revenue(orders_df):
    return (
        orders_df.groupby("date")["paid_price"]
        .sum()
        .sort_index()
        .reset_index(name="revenue")
    )


def top_revenue_days(orders_df):
    revenue = daily_revenue(orders_df)
    assert revenue["revenue"].sum() == orders_df["paid_price"].sum()
    return revenue.sort_values("revenue", ascending=False).head(5)


def prepare_author_sales(books_df, orders_df):
    books = books_df.copy()
    books["author_set"] = books["author"].map(make_author_set)

    if books["id"].duplicated().any():
        raise ValueError("Duplicate book IDs need to be checked")
    sales = orders_df.merge(
        books[["id", "author_set"]],
        left_on="book_id",
        right_on="id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_book"),
        indicator=True,
    )

    if sales["_merge"].ne("both").any():
        raise ValueError("Some orders reference unknown books")
    return sales


def calculate_author_sales(sales_df):
    return sales_df.groupby("author_set")["quantity"].sum().sort_values(ascending=False)


def select_top_values(values):
    """Select all entries tied for the maximum value."""
    return values[values == values.max()]


def top_authors(books_df, orders_df):
    sales = prepare_author_sales(books_df, orders_df)
    author_sales = calculate_author_sales(sales)
    return author_sales.head(5), select_top_values(author_sales)


def prepare_customer_orders(users_df, orders_df):
    orders = orders_df.copy()
    users = users_df.copy()
    orders["user_id"] = orders["user_id"].astype("string")
    users["id"] = users["id"].astype("string")
    customer_orders = orders.merge(
        users[["id", "person_id"]],
        left_on="user_id",
        right_on="id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_user"),
    )

    if customer_orders["person_id"].isna().any():
        raise ValueError("Some orders reference unknown users")
    return customer_orders


def calculate_customer_spending(customer_orders):
    return (
        customer_orders.groupby("person_id")["paid_price"]
        .sum()
        .sort_values(ascending=False)
    )


def best_buyers(users_df, orders_df):
    orders = prepare_customer_orders(users_df, orders_df)
    spending = calculate_customer_spending(orders)
    return select_top_values(spending)
