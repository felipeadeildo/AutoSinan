import logging
import os
from pathlib import Path

import pandas as pd

from core.constants import DATA_FOLDER, EXAMS_GAL_MAP
from core.utils import clear_screen, load_data, normalize_columns, to_datetime


class SinanGalData:
    """Loads and clean the data from GAL applying some filter rules."""

    df: pd.DataFrame

    def __init__(self, logger: logging.Logger):
        self.logger = logger
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
            print(
                f"Nenhum arquivo encontrado dentro de '{self.__datafolder}'. Por favor adicione pelo menos um arquivo de dados."
            )
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
                print("Escolha inválida. Por favor, tente novamente.")
                continue
            else:
                if 1 <= choice <= len(datasets):
                    selected = datasets[choice - 1]
                    selecteds.append(selected)
                    datasets.pop(choice - 1)
                    clear_screen()
                    print(f"Datasets selecionados: {'; '.join(selecteds)}")
                else:
                    print("Escolha inválida. Por favor, tente novamente.")
                    continue
            if not datasets:
                break

        if not selecteds:
            print("Nenhum dataset selecionado.")
            exit(0)

        return selecteds

    def __get_df(self):
        """
        Get a dataframe by concatenating selected datasets.
        """
        selecteds = self.__choice_datasets()

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
        self.logger.info("EXAM_FILTERS: Filtrando exames")
        print("Filtrando pacientes que irão ser usados para alimentar o SINAN...")

        rules = {
            "IgM": lambda time: time + pd.Timedelta(days=1) >= pd.Timedelta(days=6),
            "NS1": lambda time: time <= pd.Timedelta(days=5),
            "PCR": lambda time: time <= pd.Timedelta(days=5),
        }

        self.logger.info(f"EXAM_FILTERS: Tipos de Exames: {rules.keys()}")

        def filter_content(row: pd.Series) -> bool:
            exam_type = EXAMS_GAL_MAP.get(row["Exame"])
            if not exam_type:
                print(
                    f"Tipo de examme \"{row['Exame']}\" é desconhecido. Removendo paciente."
                )
                return False

            rule = rules[exam_type]  # i believe that this will work
            elapsed_time = abs((row["Data do 1º Sintomas"] - row["Data da Coleta"]))

            result = rule(elapsed_time)
            if result:
                self.logger.info(
                    f"EXAM_FILTERS: SUCESSO: Exame {row['Paciente']} ({row['Exame']}) tem {elapsed_time.days} dias"
                )
            else:
                self.logger.info(
                    f"EXAM_FILTERS: FALHA: Exame {row['Paciente']} ({row['Exame']}) tem {elapsed_time.days} dias"
                )

            return result

        self.df = self.df[self.df.apply(filter_content, axis=1, result_type="reduce")]
        print(f"Total de pacientes hábeis para irem para o SINAN: {len(self.df)}")

    def clean_data(self):
        """
        Method to clean the data. It logs the start of the cleaning process, loads the data, logs the successful data load, and then iterates through a list of cleaning functions to clean the data.
        """
        self.logger.info("CLEAN_DATA: Limpando dados")
        print("Iniciando a limpeza dos dados...")

        cleaners = [
            self.__exam_filters,
        ]
        for fn in cleaners:
            fn()

        self.logger.info("CLEAN_DATA: Dados limpos")
        print("Limpeza concluída.")

    def load(self):
        """
        Load method to load and preprocess GAL and SINAN datasets.
        """
        # GAL
        self.logger.info("DATA_LOADER: Obtendo o dataset do GAL")
        print("Escolha o dataset do GAL para usar...")
        self.df = self.__get_df()
        self.logger.info("DATA_LOADER:Dataset do GAL obtido")

        to_normalize = ["Paciente", "Nome da Mãe"]
        self.logger.info(f"DATA_LOADER: Normalizando colunas: {to_normalize}")
        normalize_columns(self.df, to_normalize)
        self.logger.info("Colunas normalizadas")

        to_setdatetime = ["Data de Nascimento", "Data do 1º Sintomas", "Data da Coleta"]
        self.logger.info(
            f"DATA_LOADER: Convertendo colunas para datetime: {to_setdatetime}"
        )
        to_datetime(self.df, to_setdatetime, format="%d-%m-%Y")
        self.logger.info("DATA_LOADER: Colunas convertidas para datetime")

        self.clean_data()
