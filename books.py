import pandas as pd


def clean_column_names(books_df):
    books = books_df.copy()
    books.columns = books.columns.str.removeprefix(":")
    return books


def clean_publishers(books_df):
    books = books_df.copy()
    books["publisher"] = (
        books["publisher"].astype("string").str.strip().replace("", pd.NA)
    )
    return books


def clean_years(books_df):
    books = books_df.copy()
    years = pd.to_numeric(books["year"], errors="coerce")
    books["year"] = years.mask(years <= 0).astype("Int64")
    return books


def clean_books(books_df):
    books = clean_column_names(books_df)
    books = clean_publishers(books)
    return clean_years(books)


def validate_books(books_df):
    print(books_df.head())
    books_df.info()
    print("Missing values:")
    print(books_df.isna().sum())
    print("Year dtype:", books_df["year"].dtype)
    print("Missing years:", books_df["year"].isna().sum())


def make_author_set(value):
    return tuple(sorted({name.strip() for name in value.split(",") if name.strip()}))
