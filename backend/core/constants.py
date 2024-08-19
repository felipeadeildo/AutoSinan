import datetime as dt
from pathlib import Path
from typing import Literal, Mapping, TypedDict

SINAN_BASE_URL = "http://sinan.saude.gov.br"  # protocol http
"""Base url for Sinan Website."""

EXECUTION_DATE = dt.datetime.now()
"""Datetime object for the execution date and time."""

TODAY = EXECUTION_DATE.replace(hour=0, minute=0, second=0, microsecond=0)
"""Datetime object for today at midnight."""

TODAY_FORMATTED = TODAY.strftime("%d/%m/%Y")
"""Formatted date string for today. (dd/mm/yyyy)"""

TODAY_MONTH_FORMATTED = TODAY.strftime("%m/%Y")
"""Formatted date string for today. (mm/yyyy)"""

CURRENT_YEAR_FIRST_DAY = dt.date(year=TODAY.year, month=1, day=1)
"""Date object for the first day of the current year."""

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)
"""User agent string used to access the website"""


SETTINGS_FILE = "settings.toml"
"""Settings file name with the configs used by the bots."""


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
        "Não Reagente": None,
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


class NotificationType(TypedDict):
    """Represents a notification on `investigator.investigate_multiple` method. (Typescript?! LOL!)"""

    open_payload: dict
    has_investigation: bool
    notification_date: dt.datetime


PRIORITY_CLASSIFICATION_MAP: Mapping[str, int] = {
    "5": 0,
    "10": 1,
    "11": 2,
    "12": 3,
}
"""Priority classification map to the exam classification (5, 10, 11, 12)"""

CLASSIFICATION_FRIENDLY_MAP: Mapping[str, str] = {
    "5": "5 - Descartado",
    "10": "10 - Dengue",
    "11": "11 - Dengue com sinais de alarme",
    "12": "12 - Dengue grave",
}
"""A friendly map to the exam classification (5, 10, 11, 12)"""

SCRIPT_GENERATED_PATH = Path("script")
"""The path to save log files and other files."""


SCRIPT_GENERATED_PATH.mkdir(exist_ok=True)

UNIVERSAL_STATS_FILE_PATH = SCRIPT_GENERATED_PATH / "stats.json"
"""The path to save the universal statistics where will be saved the stats between executions."""


SEARCH_POSSIBLE_CRITERIAS = Literal[
    "Nome do paciente",
    "Nome da mãe",
    "Número da Notificação",
    "Data de nascimento",
]
"""[TypeHint] Possible search criteria for the notification research method."""

SEARCH_POSSIBLE_CRITERIAS_LIST: list[SEARCH_POSSIBLE_CRITERIAS] = [
    "Nome do paciente",
    "Nome da mãe",
    "Data de nascimento",
]
"""List of possible search criteria for the notification research method."""

CRITERIA_OPERATIONS: Mapping[SEARCH_POSSIBLE_CRITERIAS, list[str]] = {
    "Nome do paciente": ["Igual", "Contendo", "Iniciando em"],
    "Nome da mãe": ["Igual", "Contendo", "Iniciando em"],
    "Data de nascimento": [
        "Igual",
        "Diferente",
        "Maior",
        "Menor",
        "Maior ou igual",
        "Menor ou igual",
    ],
    "Número da Notificação": ["Igual", "Diferente"],
}
"""Possible operations for each search criteria."""

POSSIBLE_AGRAVOS = Literal["A90 - DENGUE", "A92.0 - FEBRE DE CHIKUNGUNYA"]
"""[TypeHint] Possible agravos for the app in general"""

POSSIBLE_AGRAVOS_LIST: list[POSSIBLE_AGRAVOS] = [
    "A90 - DENGUE",
    "A92.0 - FEBRE DE CHIKUNGUNYA",
]
"""List of possible agravos for the app in general"""


POSSIBLE_MUNICIPALITIES = Literal["FLORIANOPOLIS"]
"""[TypeHint] Possible municipalities where the app is running"""

POSSIBLE_MUNICIPALITIES_LIST: list[POSSIBLE_MUNICIPALITIES] = ["FLORIANOPOLIS"]
"""List of possible municipalities where the app is running"""
