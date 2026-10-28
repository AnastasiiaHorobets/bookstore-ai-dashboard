from pathlib import Path

from analytics import (
    best_buyers,
    count_author_sets,
    daily_revenue,
    top_authors,
    top_revenue_days,
)
from books import clean_books
from data_loader import read
from orders import calculate_paid_price, clean_prices, clean_timestamps
from report import print_report
from users import deduplicate_users, find_candidate_pairs, normalize_users

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_store_data(store_path):
    books_df = read(store_path / "books.yaml")
    users_df = read(store_path / "users.csv")
    orders_df = read(store_path / "orders.parquet")
    return books_df, users_df, orders_df


def clean_store_data(books_df, users_df, orders_df):
    books_df = clean_books(books_df)
    orders_df = clean_prices(orders_df)
    orders_df = calculate_paid_price(orders_df)
    orders_df = clean_timestamps(orders_df)
    normalized_users = normalize_users(users_df)
    users_df = deduplicate_users(users_df, normalized_users)
    return books_df, users_df, orders_df, normalized_users


def process_store(store_path):
    store_path = Path(store_path)
    books_df, users_df, orders_df = load_store_data(store_path)
    return clean_store_data(books_df, users_df, orders_df)


def analyze_store(books_df, users_df, orders_df, normalized_users):
    candidate_pairs = find_candidate_pairs(users_df, normalized_users)
    top_days = top_revenue_days(orders_df)
    top_five_authors, most_popular_authors = top_authors(books_df, orders_df)
    best = best_buyers(users_df, orders_df)
    revenue_df = daily_revenue(orders_df)
    unique_author_sets = count_author_sets(books_df)

    return {
        "candidate_pairs": candidate_pairs,
        "top_days": top_days,
        "top_five_authors": top_five_authors,
        "most_popular_authors": most_popular_authors,
        "best_buyers": best,
        "daily_revenue": revenue_df,
        "unique_author_sets": unique_author_sets,
    }


def find_store_paths(data_dir=DATA_DIR):
    return sorted(path for path in Path(data_dir).glob("STORE*") if path.is_dir())


def run_store(store_path):
    print(f"\n========== {store_path.name} ==========")

    books_df, users_df, orders_df, normalized_users = process_store(store_path)
    results = analyze_store(books_df, users_df, orders_df, normalized_users)
    print_report(books_df, users_df, orders_df, results)


def main():
    store_paths = find_store_paths()
    if not store_paths:
        raise FileNotFoundError(f"No STORE* directories found in {DATA_DIR}")
    for store_path in store_paths:
        run_store(store_path)


if __name__ == "__main__":
    main()
