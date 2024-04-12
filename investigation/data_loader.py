import logging
import os
from pathlib import Path

import pandas as pd

from core.constants import DATA_FOLDER, EXAMS_GAL_MAP, TODAY
from core.utils import clear_screen, load_data, normalize_columns, to_datetime


class SinanGalData:
    """Loads and clean the data from GAL and Sinan sources applying some filter rules."""

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
                f"Nenhum arquivo encontrado dentro de {self.__datafolder}. Por favor adicione pelo menos um arquivo de dados."
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
                    print(f"Dataset selecionado: {selected}")
                else:
                    print("Escolha inválida. Por favor, tente novamente.")
                    continue

        if not selecteds:
            print("Nenhum dataset selecionado.")
            exit(0)

        print(f"Datasets selecionados: {selecteds}")
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

    def __remove_duplicates(self):
        """
        Remove duplicate patients from the SINAN dataset based on specified criteria.
        """
        self.logger.info("REMOVE_DUPLICATES: Removendo duplicados")
        print("Identificando e removendo pacientes duplicados na base SINAN...")
        self.logger.info("REMOVE_DUPLICATES: Quantidade ANTES: %d", len(self.df_sin))
        print(f"Total de linhas SINAN: {len(self.df_sin)}")

        DATE_COLUMN = "DT_SIN_PRI"

        # Define the criteria for identifying duplicates
        duplicate_criteria = ["NM_PACIENT", "DT_NASC", "NM_MAE_PAC"]
        self.logger.info(
            f"REMOVE_DUPLICATES: Critério de duplicidade: {duplicate_criteria}"
        )
        MAX_NOTIFICATION_DATE_DIFF = pd.Timedelta(days=15)

        # Sort the SINAN dataset by notification date
        self.df_sin.sort_values(by=[DATE_COLUMN], inplace=True)

        # Find and mark duplicates based on the specified criteria
        duplicated_mask = self.df_sin.duplicated(subset=duplicate_criteria, keep=False)

        grouped = self.df_sin[duplicated_mask].groupby(duplicate_criteria)

        # Filter the duplicates based on the maximum notification date difference
        considered_patients_duplicates = []
        for group_name, group_index in grouped.groups.items():
            self.logger.info(
                f"REMOVE_DUPLICATES: Analisando grupo de Duplicados: {group_name}"
            )
            group = self.df_sin.loc[group_index]
            considered_patients = [group.iloc[0]]
            for _, patient in group.iloc[1:].iterrows():
                if (
                    abs(considered_patients[-1][DATE_COLUMN] - patient[DATE_COLUMN])
                    <= MAX_NOTIFICATION_DATE_DIFF
                ):
                    self.logger.info(
                        f"REMOVE_DUPLICATES: Paciente considerado duplicado: {patient['NM_PACIENT']}"
                    )
                    considered_patients.append(patient)

            considered_patients_str = "\t\n".join(
                str(p["NM_PACIENT"]) for p in considered_patients
            )

            print(
                f"Grupo de Duplicados: {group_name} foram considerados:\n{considered_patients_str}"
            )
            self.logger.info(
                f"REMOVE_DUPLICATES: Pacientes considerados duplicados:\n{considered_patients_str}"
            )
            considered_patients_duplicates.extend(considered_patients)

        df_considered_duplicates = pd.DataFrame(considered_patients_duplicates)
        df_non_duplicates = self.df_sin[~duplicated_mask]

        self.df_sin = pd.concat(
            [df_non_duplicates, df_considered_duplicates], ignore_index=True
        )
        self.df_sin.reset_index(drop=True, inplace=True)

        self.logger.info("REMOVE_DUPLICATES: Quantidade DEPOIS: %d", len(self.df_sin))

        print(f"Pacientes duplicados removidos. Total: {len(self.df_sin)}")

    def __join_datasets(self):
        """
        Join datasets based on specified criteria and update the self.df attribute with the combined data.
        """
        self.logger.info("JOIN_DATASETS: Juntando bases")
        print("Juntando as bases GAL e SINAN...")

        DATE_SIN_COLUMN = "DT_SIN_PRI"
        DATE_GAL_COLUMN = "Data do 1º Sintomas"

        # Define the maximum notification date difference (1 week)
        max_notification_date_diff = pd.Timedelta(days=7)
        new_rows = []
        rows_not_found = []

        for _, row in self.df_sin.iterrows():
            self.logger.info(
                f"JOIN_DATASETS: Paciente: Procurando exames de {row['NM_PACIENT']} nascido em {row['DT_NASC']} e mae {row['NM_MAE_PAC']}"
            )
            results = self.df_gal[
                (self.df_gal["Paciente"] == row["NM_PACIENT"])
                & (self.df_gal["Data de Nascimento"] == row["DT_NASC"])
                & (self.df_gal["Nome da Mãe"] == row["NM_MAE_PAC"])
            ]
            to_extend = []
            self.logger.info(
                f"JOIN_DATASETS: Paciente: {len(results)} resultados encontrados."
            )
            for _, result in results.iterrows():
                # Check if the notification date is within the maximum notification date difference
                notification_date_diff = abs(
                    result[DATE_GAL_COLUMN] - row[DATE_SIN_COLUMN]
                )
                # abs(x - a) <= b implies that  x is in [a - b, a + b]
                if notification_date_diff <= max_notification_date_diff:
                    self.logger.info(
                        f"JOIN_DATASETS: Exame: {row['NM_PACIENT']} encontrado. Adicionando resultado do exame {result['Exame']} na linha {len(to_extend) + 1}"
                    )
                    new_row = pd.concat([row, result])
                    to_extend.append(new_row)
                else:
                    self.logger.info(
                        f"JOIN_DATASETS: Exame: {row['NM_PACIENT']} ignorado. Diferença de {notification_date_diff} superior a {max_notification_date_diff}"
                    )

            new_rows.extend(to_extend)
            if not to_extend:
                rows_not_found.append(row)

            print(
                f"Paciente {row['NM_PACIENT']} encontrado com {len(results)} resultados dos quais {len(to_extend)} foram selecionados."
            )
            self.logger.info(
                f"JOIN_DATASETS: Paciente: {row['NM_PACIENT']} encontrado. {len(results)} resultados encontrados. {len(to_extend)} selecionados."
            )

        self.df = pd.DataFrame(new_rows)
        not_found_df = pd.DataFrame(rows_not_found)
        not_found_df.to_excel(
            f"Pacientes Sinan Não Encontrados - {TODAY.strftime('%Y%m%d_%H%M%S')}.xlsx",
            index=False,
        )

    def __exam_filters(self):
        """
        A function to filter the content of the merged dataframe based on specific exam types and their corresponding rules.

        Raise:
            Exception: If the merged dataframe is not defined yet.
        """
        self.logger.info("EXAM_FILTERS: Filtrando exames")
        print("Filtrando pacientes que irão ser usados para alimentar o SINAN...")
        if self.df is None:
            raise Exception("Merged dataframe is not defined yet.")

        rules = {
            "IgM": lambda time: time >= pd.Timedelta(days=6),
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
                    f"EXAM_FILTERS: SUCESSO: Exame {row['NM_PACIENT']} ({row['Exame']}) tem {elapsed_time.days} dias"
                )
            else:
                self.logger.info(
                    f"EXAM_FILTERS: FALHA: Exame {row['NM_PACIENT']} ({row['Exame']}) tem {elapsed_time.days} dias"
                )

            return result

        self.df = self.df[self.df.apply(filter_content, axis=1, result_type="reduce")]
        print(f"Total de pacientes hábeis para irem para o SINAN: {len(self.df)}")

    def clean_data(self):
        """
        Method to clean the data. It logs the start of the cleaning process, loads the data, logs the successful data load, and then iterates through a list of cleaning functions to clean the data.
        """
        self.logger.info("Limpando dados")
        print("Iniciando a limpeza dos dados...")

        cleaners = [
            self.__remove_duplicates,
            self.__join_datasets,
            self.__exam_filters,
        ]
        for fn in cleaners:
            fn()

        self.logger.info("Dados limpos")
        print("Limpeza concluída.")

    def load(self):
        """
        Load method to load and preprocess GAL and SINAN datasets.
        """
        # GAL
        self.logger.info("Obtendo o dataset do GAL")
        print("Escolha o dataset do GAL para usar...")
        self.df_gal = self.__get_df()
        self.logger.info("Dataset do GAL obtido")

        to_normalize = ["Paciente", "Nome da Mãe"]
        self.logger.info(f"Normalizando colunas: {to_normalize}")
        normalize_columns(self.df_gal, to_normalize)
        self.logger.info("Colunas normalizadas")

        to_setdatetime = ["Data de Nascimento", "Data do 1º Sintomas", "Data da Coleta"]
        self.logger.info(f"Convertendo colunas para datetime: {to_setdatetime}")
        to_datetime(self.df_gal, to_setdatetime, format="%d-%m-%Y")
        self.logger.info("Colunas convertidas para datetime")

        # SINAN
        self.logger.info("Obtendo o dataset do SINAN")
        print("\n\nEscolha o dataset do SINAN para usar...")
        self.df_sin = self.__get_df()
        self.logger.info("Dataset do SINAN obtido")

        to_normalize = ["NM_PACIENT", "NM_MAE_PAC"]
        self.logger.info(f"Normalizando colunas: {to_normalize}")
        normalize_columns(self.df_sin, to_normalize)

        to_setdatetime = ["DT_NASC", "DT_SIN_PRI"]
        self.logger.info(f"Convertendo colunas para datetime: {to_setdatetime}")
        to_datetime(self.df_sin, to_setdatetime)

        self.clean_data()
