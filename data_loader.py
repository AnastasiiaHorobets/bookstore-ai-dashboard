from pathlib import Path

import pandas as pd
import yaml


def read_yaml(file_path):
    with open(file_path, encoding="utf-8") as file:
        return pd.DataFrame(yaml.safe_load(file))


pd.read_yaml = read_yaml


def get_file_extension(file_path):
    return Path(file_path).suffix.lower().lstrip(".")


def read(file_path):
    ext = get_file_extension(file_path)
    reader = getattr(pd, f"read_{ext}")
    return reader(file_path)
