import json
import logging
import os
import re
from pathlib import Path
from typing import List

import pandas as pd
import requests
from bs4 import NavigableString, Tag
from dbfread import DBF
from icecream import ic

from .constants import CREDENTIALS_FILE, SCRIPT_GENERATED_PATH, TODAY


def clear_screen():
    """Clear the console screen"""
    os.system("cls" if os.name == "nt" else "clear")


def load_data(path: Path) -> pd.DataFrame:
    """Load data from file

    Args:
        path (Path): Path to file.
            Allowed extensions: `.csv`, `.xlsx`, `.dbf`

    Raises:
        ValueError: Unsupported file type

    Returns:
        pd.DataFrame: Dataframe with loaded data
    """
    ext = path.suffix
    match ext:
        case ".csv":
            return pd.read_csv(path, sep=";", encoding="latin-1")
        case ".xlsx":
            return pd.read_excel(path)
        case ".dbf":
            return pd.DataFrame(iter(DBF(path, encoding="latin-1")))
        case _:
            raise ValueError(f"Unsupported file type: {ext}")


def normalize_name(name: str) -> str:
    """Normalize name (string) to the same format (upper and no spaces)

    Args:
        name (str): Name to normalize

    Returns:
        str: Normalized name
    """
    if not isinstance(name, str):
        return name
    return re.sub(r"\s+", " ", name).strip().upper()


def normalize_columns(df: pd.DataFrame, columns: List[str]):
    """Inplace normalization of columns

    Args:
        df (pd.DataFrame): Dataframe with columns to normalize
        columns (List[str]): List of columns to normalize
    """
    for column in columns:
        df[column] = df[column].apply(lambda x: normalize_name(x))


def to_datetime(df: pd.DataFrame, columns: List[str], **kw):
    """Inplace conversion of columns to datetime

    Args:
        df (pd.DataFrame): Dataframe with columns to convert
        columns (List[str]): List of columns to convert
        **kw: Keyword arguments to pass to pd.to_datetime
    """
    for column in columns:
        df[column] = pd.to_datetime(df[column], **kw)


def valid_tag(tag: Tag | NavigableString | None) -> Tag | None:
    """Verify if a "tag" from BeautifulSoup is valid

    Args:
        tag (Tag | NavigableString | None): Tag provided by `BeautifulSoup.find()`
            or `BeautifulSoup.find_all()`

    Returns:
        Tag | None: Tag if valid, None otherwise
    """
    if not tag or isinstance(tag, NavigableString):
        return None
    return tag


def get_sinan_credentials():
    """Get Sinan credentials from file or from user input

    Returns:
        dict: A dictionary with `username` and `password` keys
    """
    credentials_path = Path(CREDENTIALS_FILE)
    if credentials_path.exists():
        with credentials_path.open() as f:
            credentials = json.load(f)
    else:
        credentials = {
            "username": input("Seu usuário: "),
            "password": input("Sua senha: "),
        }
        with credentials_path.open("w") as f:
            json.dump(credentials, f, indent=4)

    return credentials


def copy_session(session: requests.Session):
    """Copy requests session to browse over the website in parallel

    Args:
        session (requests.Session): Session to copy

    Returns:
        requests.Session: Copy of session
    """
    session_copy = requests.Session()
    session_copy.cookies.update(session.cookies)
    session_copy.headers.update(session.headers)
    session_copy.hooks.update(session.hooks)
    return session_copy


def create_logger(name: str):
    """Create a logger with the given name

    Args:
        name (str): Logger name

    Returns:
        logging.Logger: Logger
    """
    logger = logging.getLogger(name)
    fmter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler = logging.FileHandler(
        SCRIPT_GENERATED_PATH / f"{name}_{TODAY.strftime('%Y%m%d_%H%M%S')}.log"
    )
    handler.setFormatter(fmter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    ic.configureOutput(includeContext=True)
    return logger
