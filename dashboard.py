from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from openai import APIConnectionError, APIError, APITimeoutError

from ai_chat import ask_ai
from analytics import (
    best_buyers,
    count_author_sets,
    daily_revenue,
    top_authors,
    top_revenue_days,
)
from chat_tools import get_store_summary
from main import process_store

STORE_NAMES = ["STORE1", "STORE2", "STORE3", "STORE4", "STORE5"]
REVENUE_PERIODS = ["Daily", "Weekly", "Monthly"]


def configure_page():
    st.set_page_config(
        page_title="Bookstore Sales Dashboard",
        page_icon="📊",
        layout="wide",
    )
    st.title("Bookstore Sales Dashboard")


def select_store():
    return st.selectbox("Select a store", STORE_NAMES)


@st.cache_data(show_spinner="Loading store data...")
def load_store(store_name):
    store_path = Path("data") / store_name
    return process_store(store_path)


def prepare_top_days(orders_df):
    top_days = top_revenue_days(orders_df).copy()
    top_days["date"] = pd.to_datetime(top_days["date"]).dt.strftime("%Y-%m-%d")
    return top_days


def prepare_revenue(orders_df, period):
    revenue_df = daily_revenue(orders_df).copy()
    revenue_df["date"] = pd.to_datetime(revenue_df["date"])

    if period == "Weekly":
        revenue_df = (
            revenue_df.set_index("date")
            .resample("W-MON", label="left", closed="left")["revenue"]
            .sum()
            .reset_index()
        )
    elif period == "Monthly":
        revenue_df = (
            revenue_df.set_index("date").resample("MS")["revenue"].sum().reset_index()
        )

    revenue_df["revenue"] = revenue_df["revenue"].astype(float)
    return revenue_df


def build_revenue_chart(revenue_df, period):
    return (
        alt.Chart(revenue_df)
        .mark_line(
            color="#AD30DE",
            strokeWidth=1.5,
            point=alt.OverlayMarkDef(
                filled=True,
                size=12 if period == "Daily" else 35,
            ),
        )
        .encode(
            x=alt.X(
                "date:T",
                title="Date",
                axis=alt.Axis(
                    format="%d %b %Y" if period == "Daily" else "%b %Y",
                    tickCount=12 if period == "Daily" else 8,
                    labelAngle=-45 if period == "Daily" else 0,
                    labelOverlap=True,
                ),
            ),
            y=alt.Y(
                "revenue:Q",
                title="Revenue (USD)",
                scale=alt.Scale(zero=True),
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="Period starting",
                    format="%d %b %Y",
                ),
                alt.Tooltip(
                    "revenue:Q",
                    title="Revenue (USD)",
                    format=",.2f",
                ),
            ],
        )
        .properties(height=380)
    )


def render_sales_tab(orders_df):
    st.subheader("Sales Overview")
    st.write("Top 5 Days by Revenue")
    st.dataframe(prepare_top_days(orders_df), hide_index=True)

    period = st.segmented_control(
        "Revenue period",
        options=REVENUE_PERIODS,
        default="Weekly",
    )
    revenue_df = prepare_revenue(orders_df, period)
    chart = build_revenue_chart(revenue_df, period)

    st.subheader("Revenue Overview (USD)")
    st.altair_chart(chart, width="stretch")


def prepare_authors_table(top_five_authors):
    authors_table = top_five_authors.reset_index()
    authors_table["author_set"] = authors_table["author_set"].map(
        lambda names: ", ".join(names)
    )
    return authors_table


def render_most_popular_authors(most_popular_authors):
    st.write("Most Popular Author Set")
    for authors, copies in most_popular_authors.items():
        st.write(", ".join(authors))
        st.metric("Copies Sold", int(copies))


def render_authors_tab(books_df, orders_df):
    st.subheader("Authors & Books")
    st.metric("Unique Author Sets", f"{count_author_sets(books_df):,}")

    top_five_authors, most_popular_authors = top_authors(books_df, orders_df)
    render_most_popular_authors(most_popular_authors)

    st.write("Top 5 Author Sets")
    st.dataframe(
        prepare_authors_table(top_five_authors),
        hide_index=True,
    )


def find_buyer_ids(users_df, person_id):
    return sorted(
        users_df.loc[users_df["person_id"] == person_id, "id"].astype(int).tolist()
    )


def render_best_buyers(users_df, orders_df):
    st.write("Best Buyer")
    for person_id, spending in best_buyers(users_df, orders_df).items():
        st.code(str(find_buyer_ids(users_df, person_id)), language=None)
        st.metric("Total Spending (USD)", f"${spending:,.2f}")


def render_customers_tab(users_df, orders_df):
    st.subheader("Customers")
    st.metric("Unique Users", f"{users_df['person_id'].nunique():,}")
    render_best_buyers(users_df, orders_df)


def render_dashboard_tabs(books_df, users_df, orders_df):
    sales_tab, authors_tab, customers_tab = st.tabs(
        ["Sales Overview", "Authors & Books", "Customers"]
    )

    with sales_tab:
        render_sales_tab(orders_df)
    with authors_tab:
        render_authors_tab(books_df, orders_df)
    with customers_tab:
        render_customers_tab(users_df, orders_df)


def get_chat_messages(store_name):
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}

    if store_name not in st.session_state.chat_history:
        st.session_state.chat_history[store_name] = []

    return st.session_state.chat_history[store_name]


def render_chat_message(message):
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("table") is not None:
            st.dataframe(
                message["table"],
                hide_index=True,
                width="stretch",
            )


def render_chat_history(messages):
    for message in messages:
        render_chat_message(message)


def request_ai_answer(question, summary, users_df, books_df, store_name):
    return ask_ai(
        question=question,
        summary=summary,
        users_df=users_df,
        books_df=books_df,
        api_key=st.secrets["OPENROUTER_API_KEY"],
        store_name=store_name,
    )


def render_ai_answer(answer, filtered_users):
    st.write(answer)
    if filtered_users is not None:
        st.dataframe(
            filtered_users,
            hide_index=True,
            width="stretch",
        )


def process_chat_question(
    question,
    messages,
    summary,
    users_df,
    books_df,
    store_name,
):
    """Store, process, render, and save one chat exchange."""
    messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"), st.spinner("Processing request..."):
        try:
            answer, filtered_users = request_ai_answer(
                question,
                summary,
                users_df,
                books_df,
                store_name,
            )
            render_ai_answer(answer, filtered_users)
            messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "table": filtered_users,
                }
            )
        except (APIError, APIConnectionError, APITimeoutError) as error:
            st.error(f"AI request failed: {error}")


def render_ai_chat(summary, users_df, books_df, store_name):
    st.divider()
    st.subheader("AI Data Assistant")
    st.caption(f"Ask questions or filter data in {store_name}")

    messages = get_chat_messages(store_name)
    render_chat_history(messages)

    question = st.chat_input("Ask a question or request a data filter...")
    if question:
        process_chat_question(
            question,
            messages,
            summary,
            users_df,
            books_df,
            store_name,
        )


def run_dashboard():
    configure_page()
    store_name = select_store()
    books_df, users_df, orders_df, _normalized_users = load_store(store_name)
    render_dashboard_tabs(books_df, users_df, orders_df)
    summary = get_store_summary(books_df, users_df, orders_df)
    render_ai_chat(summary, users_df, books_df, store_name)


if __name__ == "__main__":
    run_dashboard()
