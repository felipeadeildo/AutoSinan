import os
import re
from pathlib import Path
from typing import List

import pandas as pd
import requests
import toml
from bs4 import NavigableString, Tag
from dbfread import DBF

from .constants import (
    CRITERIA_OPERATIONS,
    CURRENT_YEAR_FIRST_DAY,
    POSSIBLE_AGRAVOS,
    POSSIBLE_AGRAVOS_LIST,
    SEARCH_POSSIBLE_CRITERIAS_LIST,
    SETTINGS_FILE,
    TODAY_FORMATTED,
    TODAY_MONTH_FORMATTED,
)


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


def __create_initial_settings():
    print("Sobre o Sinan Online:")
    credentials = {
        "username": input("Usuário: "),
        "password": input("Senha: "),
    }

    print("Sobre as Investigações: ")
    print("Escolha qual agravo será utilizado:")
    for i, agravo in enumerate(POSSIBLE_AGRAVOS_LIST, 1):
        print(f"\t{i} - {agravo}")
    agravo = POSSIBLE_AGRAVOS_LIST[int(input("Agravo: ")) - 1]

    print(
        "Sobre os critérios de pesquisa de paciente escolha quais devem ser utilizados e suas operações:"
    )
    criterias = {}
    for criteria in SEARCH_POSSIBLE_CRITERIAS_LIST:
        use_criteria = (
            input(f"O bot pode usar o critério '{criteria}'? (s/n): ").lower() == "s"
        )
        if use_criteria:
            possible_operations = CRITERIA_OPERATIONS[criteria]
            print("\tEscolha qual operação deve ser realizada para o critério:")
            for i, operation in enumerate(possible_operations, 1):
                print(f"\t{i} - {operation}")
            operation = possible_operations[int(input("Operação: ")) - 1]
        else:
            operation = None

        criterias[criteria] = {"operacao": operation, "pode_usar": use_criteria}

    criterias["Número da Notificação"] = {"operacao": "Igual", "pode_usar": True}

    investigacao = {
        "agravo": agravo,
        "criterios": criterias,
    }

    return {
        "sinan_credentials": credentials,
        "sinan_investigacao": investigacao,
    }


def get_settings():
    """Get the configuration setted in `settings.toml`

    Returns:
        dict: Configuration document
    """
    config_path = Path(SETTINGS_FILE)
    if config_path.exists():
        with config_path.open() as f:
            settings = toml.load(f)
    else:
        settings = __create_initial_settings()

        with config_path.open("w") as f:
            toml.dump(settings, f)

    return settings


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


def generate_search_base_payload(agravo: POSSIBLE_AGRAVOS):
    """Generate base payload for Notification Researcher

    Args:
        agravo (str): Agravo to filter by (eg. A90 - DENGUE)

    Returns:
        dict: Base payload to use in payload construction
    """
    return {
        "AJAXREQUEST": "_viewRoot",
        "form": "form",
        "form:consulta_tipoPeriodo": "0",
        "form:consulta_dataInicialInputDate": CURRENT_YEAR_FIRST_DAY.strftime(
            "%d/%m/%Y"
        ),
        "form:consulta_dataInicialInputCurrentDate": TODAY_MONTH_FORMATTED,
        "form:consulta_dataFinalInputDate": TODAY_FORMATTED,
        "form:consulta_dataFinalInputCurrentDate": TODAY_MONTH_FORMATTED,
        "form:richagravocomboboxField": agravo,
        "form:richagravo": agravo,
        "form:tipoUf": "3",  # Notificação ou Residência
        "form:consulta_uf": "24",  # SC
        "form:tipoSaida": "2",  # Lista de Notificação
        "form:consulta_tipoCampo": "0",
        "form:consulta_municipio_uf_id": "0",
    }
