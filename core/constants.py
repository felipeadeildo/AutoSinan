import datetime as dt
from typing import Literal, Mapping

SINAN_BASE_URL = "http://sinan.saude.gov.br"  # protocol http
"""Base url for Sinan Website."""

TODAY = dt.datetime.now()
"""Datetime object for today."""

CURRENT_YEAR_FIRST_DAY = dt.date(year=TODAY.year, month=1, day=1)
"""Date object for the first day of the current year."""


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)
"""User agent string used to access the website"""


CREDENTIALS_FILE = "credentials.json"
"""Credentials file name with the credentials to access the website"""


DATA_FOLDER = "dados"
"""Folder name to store the datasets used by the bots."""

POSSIBLE_EXAM_TYPES = Literal["IgM", "NS1", "PCR"]

EXAMS_GAL_MAP: dict[str, POSSIBLE_EXAM_TYPES] = {
    "Dengue, IgM": "IgM",
    "Dengue, Detecção de Antígeno NS1": "NS1",
    "Dengue, Biologia Molecular": "PCR",
    "Pesquisa de Arbovírus (ZDC)": "PCR",
}
"""Exam mapping for the Gal dataset."""

EXAM_VALUE_COL_MAP: dict[POSSIBLE_EXAM_TYPES, str] = {
    "IgM": "Resultado",
    "NS1": "Resultado",
    "PCR": "Dengue",
}
"""Represents the column name of the exam value in the unificated dataset."""

# 5 = Descartado; 10 = Dengue
CLASSSIFICATION_MAP: Mapping[POSSIBLE_EXAM_TYPES, Mapping[str, str | None]] = {
    "IgM": {
        "Não Reagente": "5",
        "Reagente": "10",
        "Indeterminado": None,
    },
    "PCR": {
        "Não Detectável": "5",
        "Detectável": "10",
        "_default": None,
    },
    "NS1": {
        "Não Reagente": "5",
        "Reagente": "10",
        "Indeterminado": None,
    },
}
"""Classification map to the GAL Exam Result."""


EXAM_RESULT_ID: Mapping[POSSIBLE_EXAM_TYPES, Mapping[str, str]] = {
    "PCR": {
        "Não Detectável": "2",  # Negativo
        "Detectável": "1",  # Positivo
        "_default": "3",  # Inconclusivo
    },
    "IgM": {
        "Não Reagente": "2",  # Não Reagente
        "Reagente": "1",  # Reagente
        "Indeterminado": "3",  # Inconclusivo
    },
    "NS1": {
        "Reagente": "1",  # Positivo
        "Não Reagente": "2",  # Negativo
        "Indeterminado": "3",  # Inconclusivo
    },
}
"""Input value map for the exam result in unificated dataset to Sinan Investigation Form"""
