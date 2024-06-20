import os
import time
from pathlib import Path

import pandas as pd

from core.constants import DATA_FOLDER
from core.utils import Printter, clear_screen, load_data, normalize_columns, to_datetime
from investigation.report import Report

display = Printter("DADOS")


class SinanGalData:
    """Loads and cleans the data from GAL applying some filter rules."""

    df: pd.DataFrame

    def __init__(self, settings: dict, reporter: Report):
        """Initializes SinanGalData with settings and a reporter.

        Args:
            settings (dict): Configuration settings.
            reporter (Report): Report object for logging.
        """
        self.settings = settings
        self.reporter = reporter

        self.__datafolder = Path(DATA_FOLDER)
        if not self.__datafolder.exists():
            self.__datafolder.mkdir()

    def __choice_datasets(self):
        """Chooses datasets from a specified folder and returns the selected datasets.

        Returns:
            list: List of selected datasets.
        """
        selecteds = []
        datasets = os.listdir(self.__datafolder)
        if len(datasets) == 0:
            display(f"Nenhum arquivo encontrado dentro de '{self.__datafolder}'.")
            display("Por favor adicione pelo menos um arquivo de dados.")
            exit(1)

        while True:
            for i, dataset in enumerate(datasets, 1):
                display(f"{i:2} - {dataset}")
            try:
                choice = input(
                    "Selecione um dos datasets ['Enter' para parar]: "
                ).strip()
                if not choice:
                    break
                choice = int(choice)
            except ValueError:
                display(
                    "Escolha inválida. Por favor, tente novamente.", category="erro"
                )
                continue
            else:
                if 1 <= choice <= len(datasets):
                    selected = datasets[choice - 1]
                    selecteds.append(selected)
                    datasets.pop(choice - 1)
                    clear_screen()
                    display(
                        f"Bases de dados selecionadas: {'; '.join(selecteds)}",
                    )
                else:
                    display(
                        "Escolha inválida. Por favor, tente novamente.",
                        category="erro",
                    )
                    continue
            if not datasets:
                break

        if not selecteds:
            display("Nenhuma base de dados foi selecionada.", category="erro")
            exit(0)

        return selecteds

    def __get_df(self):
        """Gets a dataframe by concatenating selected datasets.

        Returns:
            pd.DataFrame: Concatenated dataframe.
        """
        selecteds = self.__choice_datasets()
        self.reporter.debug(f"Bases do GAL Selecionadas: {'; '.join(selecteds)}")

        dfs = [load_data(self.__datafolder / dataset) for dataset in selecteds]

        return pd.concat(dfs, ignore_index=True)

    def load(self):
        """Loads and preprocesses GAL and SINAN datasets."""
        display("Escolha os datasets do GAL a serem carregados:")
        self.df = self.__get_df()

        start_date = time.time()
        to_normalize = ["Paciente", "Nome da Mãe"]
        normalize_columns(self.df, to_normalize)
        self.reporter.debug(f"Colunas da base do GAL normalizadas: {to_normalize}")

        to_setdatetime = [
            "Data de Nascimento",
            "Data do 1º Sintomas",
            "Data da Coleta",
            "Data da Liberação",
        ]
        to_datetime(self.df, to_setdatetime, format="%d-%m-%Y")
        self.reporter.debug(
            f"Colunas da base do GAL convertidas para datetime: {to_setdatetime}"
        )

        end_date = time.time()
        elapsed_time = end_date - start_date

        display(
            f"Datasets do GAL carregados, normalizados e filtrados em {elapsed_time:.2f} segundos."
        )
