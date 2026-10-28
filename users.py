from itertools import combinations

import pandas as pd

USER_FIELDS = ["name", "address", "phone", "email"]


def normalize_users(users_df):
    normalized = users_df[USER_FIELDS].copy()

    for column in USER_FIELDS:
        normalized[column] = normalize_text(normalized[column])
    normalized["phone"] = normalize_phone(normalized["phone"])
    return normalized


def normalize_text(series):
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.casefold()
        .replace("", pd.NA)
    )


def normalize_phone(series):
    return series.str.replace(r"\D", "", regex=True).replace("", pd.NA)


#  Find the representative of a user group
def find_root(parent, index):
    while parent[index] != index:
        parent[index] = parent[parent[index]]
        index = parent[index]
    return index


def union_users(parent, first, second):
    first_root = find_root(parent, first)
    second_root = find_root(parent, second)
    parent[second_root] = first_root


def merge_matching_users(parent, normalized_users, fields):
    seen = {}

    for row in normalized_users[list(fields)].itertuples(index=True, name=None):
        index, *values = row
        if any(pd.isna(value) for value in values):
            continue

        key = tuple(values)
        if key in seen:
            union_users(parent, seen[key], index)
        else:
            seen[key] = index


def build_user_groups(normalized_users):
    parent = {index: index for index in normalized_users.index}

    for fields in combinations(USER_FIELDS, 3):
        merge_matching_users(parent, normalized_users, fields)
    return parent


def assign_person_ids(users_df, parent):
    users = users_df.copy()
    users["person_id"] = [
        str(users.loc[find_root(parent, index), "id"]) for index in users.index
    ]
    return users


# Deduplicate users using normalized fields
def deduplicate_users(users_df, normalized_users):
    parent = build_user_groups(normalized_users)
    return assign_person_ids(users_df, parent)


def has_missing_address(normalized_users, first, second):
    return pd.isna(normalized_users.loc[first, "address"]) or pd.isna(
        normalized_users.loc[second, "address"]
    )


def find_candidate_pairs(users_df, normalized_users):
    candidates = set()

    for fields in combinations(["name", "phone", "email"], 2):
        groups = normalized_users.groupby(list(fields), dropna=True)

        for _, group in groups:
            for first, second in combinations(group.index, 2):
                if (
                    users_df.loc[first, "person_id"]
                    == users_df.loc[second, "person_id"]
                ):
                    continue

                if has_missing_address(normalized_users, first, second):
                    candidates.add(tuple(sorted((first, second))))
    return candidates
