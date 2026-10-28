from books import validate_books
from orders import validate_orders


def print_data_validation(books_df, orders_df):
    validate_books(books_df)
    validate_orders(orders_df)


def print_candidate_pairs(users_df, pairs):
    print("Pairs needing review:", len(pairs))

    for first, second in sorted(pairs)[:5]:
        columns = ["id", "name", "address", "phone", "email", "person_id"]
        print(users_df.loc[[first, second], columns].to_string(index=False))
        print()


def print_revenue_report(results):
    print("\nTop 5 days by revenue (USD):")
    print(results["top_days"].to_string(index=False))


def print_author_report(results):
    print("\nTop 5 author sets by copies sold:")
    print(results["top_five_authors"])
    print("\nMost popular author set(s):")
    print(results["most_popular_authors"])


def print_best_buyers(users_df, best_buyers):
    for person_id, total_spent in best_buyers.items():
        ids = users_df.loc[users_df["person_id"] == person_id, "id"]
        print("Best buyer IDs:", sorted(ids.astype(int).tolist()))
        print("Total spending (USD):", total_spent)


def print_additional_metrics(results):
    print("\nDaily revenue sample:")
    print(results["daily_revenue"].head())
    print("Unique author sets:", results["unique_author_sets"])


def print_report(books_df, users_df, orders_df, results):
    print_data_validation(books_df, orders_df)
    print_candidate_pairs(users_df, results["candidate_pairs"])
    print_revenue_report(results)
    print_author_report(results)
    print_best_buyers(users_df, results["best_buyers"])
    print_additional_metrics(results)
