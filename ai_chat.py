import json

from openai import OpenAI

from chat_tools import (
    filter_books_by_person_names,
    filter_users_by_email_prefix,
)

MODEL = "openrouter/free"

SYSTEM_PROMPT = (
    "You are a bookstore data assistant. "
    "Always use tools for questions about store data. "
    "Never invent results. "
    "For email filtering use filter_users_by_email_prefix. "
    "For books containing people's names use "
    "filter_books_by_person_names. "
    "Multiple user IDs in one best_buyers entry belong "
    "to the same real customer. "
    "Keep answers concise and natural. "
    "Do not output XML tags. "
    "The application displays filtered records in a table. "
    "Answer in the user's language."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_store_data",
            "description": "Get verified bookstore analytics.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_users_by_email_prefix",
            "description": "Display users filtered by email prefixes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prefixes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["prefixes"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_books_by_person_names",
            "description": ("Display books with people's names in titles."),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
]


def create_client(api_key):
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        timeout=30.0,
        max_retries=0,
    )


def build_messages(question, store_name):
    return [
        {
            "role": "system",
            "content": (
                f"{SYSTEM_PROMPT} "
                f"The selected store is {store_name}. "
                "All tool results belong exclusively to this store. "
                "They are not totals across all stores."
            ),
        },
        {"role": "user", "content": question},
    ]


def request_tools(client, messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )
    return response.choices[0].message


def validate_no_arguments(arguments):
    if arguments:
        raise ValueError("Unexpected tool arguments")


def validate_prefixes(arguments):
    prefixes = arguments.get("prefixes")
    if not isinstance(prefixes, list) or not prefixes:
        raise ValueError("Invalid email prefixes")
    if not all(isinstance(p, str) and p.strip() for p in prefixes):
        raise ValueError("Invalid email prefixes")
    return prefixes


def run_summary(arguments, summary):
    validate_no_arguments(arguments)
    return summary, None


def run_user_filter(arguments, users_df):
    prefixes = validate_prefixes(arguments)
    table = filter_users_by_email_prefix(users_df, prefixes)
    result = {"prefixes": prefixes, "matching_users": len(table)}
    return result, table


def run_book_filter(arguments, books_df):
    validate_no_arguments(arguments)
    table = filter_books_by_person_names(books_df)
    result = {"matching_books": len(table)}
    return result, table


def execute_tool(name, arguments, summary, users_df, books_df):
    handlers = {
        "get_store_data": lambda: run_summary(arguments, summary),
        "filter_users_by_email_prefix": lambda: run_user_filter(arguments, users_df),
        "filter_books_by_person_names": lambda: run_book_filter(arguments, books_df),
    }
    if name not in handlers:
        raise ValueError(f"Unknown tool: {name}")
    return handlers[name]()


def add_tool_result(messages, call, result):
    messages.append(
        {
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result),
        }
    )


def process_tool_calls(message, messages, summary, users_df, books_df):
    tables = []
    messages.append(message.model_dump(exclude_none=True))

    for call in message.tool_calls:
        arguments = json.loads(call.function.arguments or "{}")
        result, table = execute_tool(
            call.function.name, arguments, summary, users_df, books_df
        )
        print(f"FUNCTION CALLED: {call.function.name}", flush=True)
        add_tool_result(messages, call, result)
        if table is not None:
            tables.append(table)

    return tables[-1] if tables else None


def generate_answer(client, messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tool_choice="none",
    )
    return response.choices[0].message.content or "No answer generated."


def ask_ai(question, summary, users_df, books_df, api_key, store_name):
    client = create_client(api_key)
    messages = build_messages(question, store_name)
    message = request_tools(client, messages)

    if not message.tool_calls:
        return message.content or "No tool was called.", None

    table = process_tool_calls(message, messages, summary, users_df, books_df)
    return generate_answer(client, messages), table
