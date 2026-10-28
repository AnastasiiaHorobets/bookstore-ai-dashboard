from functools import lru_cache

import spacy

from analytics import (
    best_buyers,
    count_author_sets,
    top_authors,
    top_revenue_days,
)


# Store summary
def get_top_days(orders_df):
    days = top_revenue_days(orders_df)
    return [
        {"date": str(row.date), "revenue_usd": str(row.revenue)}
        for row in days.itertuples(index=False)
    ]


def get_popular_authors(books_df, orders_df):
    _, authors = top_authors(books_df, orders_df)
    return [
        {"authors": list(names), "copies_sold": int(copies)}
        for names, copies in authors.items()
    ]


def get_buyer_ids(users_df, person_id):
    ids = users_df.loc[users_df["person_id"] == person_id, "id"]
    return sorted(ids.astype(int).tolist())


def get_best_buyers(users_df, orders_df):
    buyers = best_buyers(users_df, orders_df)
    return [
        {
            "user_ids": get_buyer_ids(users_df, person_id),
            "total_spending_usd": str(spending),
        }
        for person_id, spending in buyers.items()
    ]


def get_store_summary(books_df, users_df, orders_df):
    return {
        "unique_users": int(users_df["person_id"].nunique()),
        "unique_author_sets": int(count_author_sets(books_df)),
        "total_revenue_usd": str(orders_df["paid_price"].sum()),
        "top_revenue_days": get_top_days(orders_df),
        "most_popular_authors": get_popular_authors(books_df, orders_df),
        "best_buyers": get_best_buyers(users_df, orders_df),
    }


# User
def normalize_prefixes(prefixes):
    return tuple(
        p.strip().lower() for p in prefixes if isinstance(p, str) and p.strip()
    )


def filter_users_by_email_prefix(users_df, prefixes):
    prefixes = normalize_prefixes(prefixes)
    if not prefixes:
        return users_df.iloc[0:0].copy()

    emails = users_df["email"].astype("string").str.strip().str.lower()
    return users_df.loc[emails.str.startswith(prefixes, na=False)].copy()


# Book
@lru_cache(maxsize=1)
def get_nlp_model():
    return spacy.load("en_core_web_sm")


def extract_person_names(doc):
    return [entity.text for entity in doc.ents if entity.label_ == "PERSON"]


def find_names_in_titles(books_df):
    nlp = get_nlp_model()
    titles = books_df["title"].fillna("").astype(str)
    return [extract_person_names(doc) for doc in nlp.pipe(titles, batch_size=64)]


def filter_books_by_person_names(books_df):
    result = books_df.copy()
    result["person_names"] = find_names_in_titles(books_df)
    return result.loc[result["person_names"].map(bool)].copy()
