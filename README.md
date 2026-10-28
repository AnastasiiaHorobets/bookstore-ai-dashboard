# Bookstore AI Dashboard

The project works with data from five stores. Each store has information about books, users, and orders.

### What it does

- Loads and cleans CSV, YAML, and Parquet files.
- Calculates daily revenue and finds the top 5 days.
- Identifies unique customers, including users with different names or contact details.
- Finds the most popular authors and the customers who spent the most.
- Displays the results in an interactive dashboard.

I also added an AI chat using OpenRouter. It can answer questions about the data by calling Python functions and filter tables based on user requests.

### Tools

Python, Pandas, Streamlit, Altair, spaCy, OpenRouter API.

### How to run

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` and add your OpenRouter API key:

```toml
OPENROUTER_API_KEY = "your_api_key"
```

Start the dashboard:

```bash
streamlit run dashboard.py
```

### Dashboard

[Live Dashboard](https://bookstore-ai-dashboard.streamlit.app)