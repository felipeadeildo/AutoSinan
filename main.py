import logging
import os
import re
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    handlers=[logging.StreamHandler()],
)


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
            return pd.read_csv(path)
        case ".xlsx":
            return pd.read_excel(path)
        case _:
            raise ValueError(f"Unsupported file type: {ext}")


def normalize_name(name: str) -> str:
    """Normalize name (string) to the same format (upper and no spaces)

    Args:
        name (str): Name to normalize

    Returns:
        str: Normalized name
    """
    return re.sub(r"\s+", " ", name).strip().upper()


class Data:
    """Loads and clean the data from GAL and Sinan sources applying some filter rules."""

    def __init__(self):
        self.__datafolder = Path("dados/")
        if not self.__datafolder.exists():
            self.__datafolder.mkdir()
        self.df = None
        self.load()

    def __choice_datasets(self):
        """
        Chooses datasets from a specified folder and returns the selected datasets.
        """
        selecteds = []
        datasets = os.listdir(self.__datafolder)
        if len(datasets) == 0:
            logging.error(
                f"Nenhum arquivo encontrado dentro de {self.__datafolder}. Por favor adicione pelo menos um arquivo de dados."
            )
            exit(1)

        while True:
            for i, dataset in enumerate(os.listdir(self.__datafolder), 1):
                print(f"{i:2} - {dataset}")
            try:
                choice = input(
                    "Selecione um dos datasets [`Enter` para parar]: "
                ).strip()
                if not choice:
                    break
                choice = int(choice)
            except ValueError:
                print("Escolha inválida. Por favor, tente novamente.")
                continue
            else:
                if 1 <= choice <= len(datasets):
                    selecteds.append(datasets[choice - 1])
                else:
                    print("Escolha inválida. Por favor, tente novamente.")
                    continue

        if not selecteds:
            logging.error("Nenhum dataset selecionado.")
            exit(0)

        logging.info(f"Datasets selecionados: {selecteds}")
        return selecteds

    def __get_df(self):
        """
        Get a dataframe by concatenating selected datasets.
        """
        selecteds = self.__choice_datasets()
        return pd.concat(
            [self.__datafolder / dataset for dataset in selecteds],
            ignore_index=True,
        )

    def __remove_duplicates(self):
        """
        Remove duplicate patients from the SINAN dataset based on specified criteria.
        """
        logging.info(
            "Identificando e removendo pacientes duplicados na base SINAN..."
        )
        logging.info(f"Total de linhas SINAN: {len(self.df_sin)}")

        DATE_COLUMN = "DT_SIN_PRI"

        # Define the criteria for identifying duplicates
        duplicate_criteria = ["NM_PACIENT", "DT_NASC", "NM_MAE_PAC"]
        max_notification_date_diff = pd.Timedelta(days=15)

        # Sort the SINAN dataset by notification date
        self.df_sin.sort_values(by=[DATE_COLUMN], inplace=True)

        # Find and mark duplicates based on the specified criteria
        is_duplicate = self.df_sin.duplicated(
            subset=duplicate_criteria, keep="first"
        )

        # Iterate through the dataset to handle duplicates
        for index, row in self.df_sin.iterrows():
            if is_duplicate[index]:  # type: ignore [__getitem__ is defined]
                # Check for duplicates within a maximum notification date difference
                notification_date = row[DATE_COLUMN]
                duplicates_within_range = self.df_sin[
                    (self.df_sin[duplicate_criteria] == row[duplicate_criteria])
                    & (
                        self.df_sin[DATE_COLUMN] - notification_date
                        <= max_notification_date_diff
                    )
                ]

                # Identify the duplicates and mark them as needed
                if len(duplicates_within_range) > 1:
                    # Handle the duplicates (e.g., choose one, merge data, or mark)
                    # Here, we're just marking them for removal
                    self.df_sin.at[index, "is_duplicate"] = True

        # Remove the marked duplicate rows
        self.df_sin = self.df_sin[~self.df_sin["is_duplicate"]]

        # Cleanup: remove the temporary 'is_duplicate' column
        self.df_sin.drop(columns=["is_duplicate"], inplace=True)

        logging.info(
            f"Pacientes duplicados removidos. Total: {len(self.df_sin)}"
        )

    def __join_datasets(self):
        """
        Join datasets based on specified criteria and update the self.df attribute with the combined data.
        """
        logging.info("Juntando as bases GAL e SINAN...")

        DATE_SIN_COLUMN = "DT_SIN_PRI"
        DATE_GAL_COLUMN = "Data de Inicio dos Sintomas"

        # Define the maximum notification date difference (1 week)
        max_notification_date_diff = pd.Timedelta(days=7)
        new_rows = []

        for _, row in self.df_sin.iterrows():
            results = self.df_gal[
                (self.df_gal["Nome do Paciente"] == row["NM_PACIENT"])
                & (self.df_gal["Data de Nascimento"] == row["DT_NASC"])
                & (self.df_gal["Nome da Mãe"] == row["NM_MAE_PAC"])
            ]
            to_extend = []
            for _, result in results.iterrows():
                if (
                    abs(result[DATE_GAL_COLUMN] - row[DATE_SIN_COLUMN])
                    <= max_notification_date_diff
                ):  # abs(x - a) <= b implies that  x is in [a - b, a + b]
                    new_row = pd.concat([row, result])
                    to_extend.append(new_row)

            new_rows.extend(to_extend)

            logging.debug(
                f"Paciente {row['NM_PACIENT']} encontrado com {len(results)} resultados dos quais {len(to_extend)} foram selecionados."
            )

        self.df = pd.DataFrame(new_rows)

    def __exam_filters(self):
        """
        A function to filter the content of the merged dataframe based on specific exam types and their corresponding rules.

        Raise:
            Exception: If the merged dataframe is not defined yet.
        """
        logging.info(
            "Filtrando pacientes que irão ser usados para alimentar o SINAN..."
        )
        if not self.df:
            raise Exception("Merged dataframe is not defined yet.")

        exams_map = {
            "Dengue, IgM": "IgM",
            "Dengue, Detecção de Antígeno NS1": "NS1",
            "Dengue, Biologia Molecular": "PCR",
        }

        rules = {
            "IgM": lambda time: time >= pd.Timedelta(days=6),
            "NS1": lambda time: time <= pd.Timedelta(days=5),
            "PCR": lambda time: time <= pd.Timedelta(days=5),
        }

        def filter_content(row: pd.Series) -> bool:
            exam_type = exams_map.get(row["Exame"])
            if not exam_type:
                logging.error(
                    f"Tipo de examme \"{row['Exame']}\" é desconhecido. Removendo paciente."
                )
                return False

            rule = rules[exam_type]  # i believe that this will work
            elapsed_time = abs(
                (
                    row["Data dos Primeiros Sintomas"] - row["Data da Coleta"]
                ).days
            )

            return rule(elapsed_time)

        self.df = self.df[
            self.df.apply(filter_content, axis=1, result_type="reduce")
        ]
        logging.info(
            f"Total de pacientes para abeis para irem para o SINAN: {len(self.df)}"
        )

    def clean_data(self):
        """
        Method to clean the data. It logs the start of the cleaning process, loads the data, logs the successful data load, and then iterates through a list of cleaning functions to clean the data.
        """
        logging.info("Iniciando a limpeza dos dados...")
        self.load()
        logging.info("Dados carregados.")

        cleaners = [
            self.__remove_duplicates,
            self.__join_datasets,
            self.__exam_filters,
        ]
        for fn in cleaners:
            fn()
        logging.info("Limpeza concluída.")

    def load(self):
        """
        Load method to load and preprocess GAL and SINAN datasets.
        """
        # GAL
        print("Escolha o dataset do GAL para usar...")
        self.df_gal = self.__get_df()
        self.df_gal["Nome do Paciente"] = self.df_gal["Nome do Paciente"].apply(
            lambda x: normalize_name(x)
        )
        self.df_gal["Nome da Mãe"] = self.df_gal["Nome da Mãe"].apply(
            lambda x: normalize_name(x)
        )
        self.df_gal["Data de Nascimento"] = pd.to_datetime(
            self.df_gal["Data de Nascimento"]
        )
        self.df_gal["Data de Inicio dos Sintomas"] = pd.to_datetime(
            self.df_gal["Data de Inicio dos Sintomas"]
        )
        self.df_gal["Data da Coleta"] = pd.to_datetime(
            self.df_gal["Data da Coleta"]
        )

        # SINAN
        print("Escolha o dataset do SINAN para usar...")
        self.df_sin = self.__get_df()
        self.df_sin["NM_PACIENT"] = self.df_sin["NM_PACIENT"].apply(
            lambda x: normalize_name(x)
        )
        self.df_sin["NM_MAE_PAC"] = self.df_sin["NM_MAE_PAC"].apply(
            lambda x: normalize_name(x)
        )
        self.df_sin["DT_NASC"] = pd.to_datetime(self.df_sin["DT_NASC"])
        self.df_sin["DT_SIN_PRI"] = pd.to_datetime(self.df_sin["DT_SIN_PRI"])

        self.clean_data()


class Sinan:
    """Sinan client taht will be used to interact with the Sinan Website doing things like:
    - Login
    - Filling out forms
    - Verifying submitted forms
    """

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    def _get_data(self):
        self.data = Data()
        self.data.load()

    def _login(self): ...

    def fill(self): ...
