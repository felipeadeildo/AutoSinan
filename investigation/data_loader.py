import os
import time
from pathlib import Path

import pandas as pd

from core.constants import DATA_FOLDER, EXAMS_GAL_MAP
from core.utils import clear_screen, load_data, normalize_columns, to_datetime
from investigation.report import Report


class SinanGalData:
    """Loads and clean the data from GAL applying some filter rules."""

    df: pd.DataFrame

    def __init__(self, settings: dict, reporter: Report):
        self.settings = settings
        self.reporter = reporter

        self.__datafolder = Path(DATA_FOLDER)
        if not self.__datafolder.exists():
            self.__datafolder.mkdir()

    def __choice_datasets(self):
        """
        Chooses datasets from a specified folder and returns the selected datasets.
        """
        selecteds = []
        datasets = os.listdir(self.__datafolder)
        if len(datasets) == 0:
            print(f"[DADOS] Nenhum arquivo encontrado dentro de '{self.__datafolder}'.")
            print("[DADOS] Por favor adicione pelo menos um arquivo de dados.")
            exit(1)

        while True:
            for i, dataset in enumerate(datasets, 1):
                print(f"{i:2} - {dataset}")
            try:
                choice = input(
                    "Selecione um dos datasets ['Enter' para parar]: "
                ).strip()
                if not choice:
                    break
                choice = int(choice)
            except ValueError:
                print("[DADOS] Escolha inválida. Por favor, tente novamente.")
                continue
            else:
                if 1 <= choice <= len(datasets):
                    selected = datasets[choice - 1]
                    selecteds.append(selected)
                    datasets.pop(choice - 1)
                    clear_screen()
                    print(
                        f"[DADOS] Bases de dados selecionadas: {'; '.join(selecteds)}"
                    )
                else:
                    print("[DADOS] Escolha inválida. Por favor, tente novamente.")
                    continue
            if not datasets:
                break

        if not selecteds:
            print("[DADOS] Nenhuma base de dados foi selecionada.")
            exit(0)

        return selecteds

    def __get_df(self):
        """
        Get a dataframe by concatenating selected datasets.
        """
        selecteds = self.__choice_datasets()
        self.reporter.debug(f"Bases do GAL Selecionadas: {'; '.join(selecteds)}")

        dfs = [
            load_data(
                self.__datafolder / dataset,
            )
            for dataset in selecteds
        ]

        return pd.concat(
            dfs,
            ignore_index=True,
        )

    def __exam_filters(self):
        """
        A function to filter the content of the merged dataframe based on specific exam types and their corresponding rules.

        Raise:
            Exception: If the merged dataframe is not defined yet.
        """
        start_time = time.time()
        patients_after_filter = len(self.df)
        print(
            "[DADOS] Filtrando exames de pacientes que podem ir para a investigação (Filtro Oportuno)."
        )

        rules = {
            "IgM": lambda time: time + pd.Timedelta(days=1) >= pd.Timedelta(days=6),
            "NS1": lambda time: time <= pd.Timedelta(days=5),
            "PCR": lambda time: time <= pd.Timedelta(days=5),
        }

        def filter_content(row: pd.Series) -> bool:
            self.reporter.set_patient(row.to_dict())
            exam_type = EXAMS_GAL_MAP.get(row["Exame"])
            if not exam_type:
                self.reporter.error(
                    f"O bot não conhece o tipo de exame {row['Exame']}",
                    observation="Paciente removido do procedimento do bot.",
                )
                return False

            rule = rules[exam_type]  # i believe that this will work
            elapsed_time = abs((row["Data do 1º Sintomas"] - row["Data da Coleta"]))

            result = rule(elapsed_time)
            if result:
                self.reporter.debug(
                    "Pode ir para a investigação no Sinan segundo o filtro oportuno.",
                    observation=f"Diferença entre data da coleta e data do 1º sintoma é de {elapsed_time.days} dias.",
                )
            else:
                self.reporter.debug(
                    "Não pode ir para a investigação no Sinan segundo o filtro oportuno.",
                    observation=f"Diferença entre data da coleta e data do 1º sintoma é de {elapsed_time.days} dias.",
                )

            return result

        self.df = self.df[self.df.apply(filter_content, axis=1, result_type="reduce")]

        end_time = time.time()

        self.reporter.clean_patient()
        elapsed_time = end_time - start_time
        self.reporter.debug(
            f"Filtro oportuno concluído em {elapsed_time:.2f} segundos.",
            observation=f"Total de pacientes hábeis para investigação no Sinan: {len(self.df)} de {patients_after_filter}.",
        )

        print(
            f"[DADOS] Filtro oportuno concluído em {elapsed_time:.2f} segundos com {len(self.df)} de {patients_after_filter} exames."
        )

    def clean_data(self):
        """
        Method to clean the data. It logs the start of the cleaning process, loads the data, logs the successful data load, and then iterates through a list of cleaning functions to clean the data.
        """
        cleaners = [
            self.__exam_filters,
        ]
        for fn in cleaners:
            fn()

    def load(self):
        """
        Load method to load and preprocess GAL and SINAN datasets.
        """
        # GAL
        print("[DADOS] Escolha os datasets do GAL a serem carregados:")
        self.df = self.__get_df()

        start_date = time.time()
        to_normalize = ["Paciente", "Nome da Mãe"]
        normalize_columns(self.df, to_normalize)
        self.reporter.debug(f"Colunas da base do GAL normalizadas: {to_normalize}")

        to_setdatetime = ["Data de Nascimento", "Data do 1º Sintomas", "Data da Coleta"]
        to_datetime(self.df, to_setdatetime, format="%d-%m-%Y")
        self.reporter.debug(
            f"Colunas da base do GAL convertidas para datetime: {to_setdatetime}"
        )

        self.clean_data()
        end_date = time.time()
        elapsed_time = end_date - start_date

        print(
            f"[DADOS] Datasets do GAL carregados, normalizados e filtrados em {elapsed_time:.2f} segundos."
        )
