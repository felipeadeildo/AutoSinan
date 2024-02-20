import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Literal

import pandas as pd
import requests
from bs4 import BeautifulSoup, NavigableString

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%y %H:%M:%S",
    handlers=[logging.FileHandler("main.log"), logging.StreamHandler()],
)

BASE_URL = "http://sinan.saude.gov.br"
TODAY = datetime.now()
FIRST_YEAR_DAY = datetime(year=TODAY.year, month=1, day=1)


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


class Data:
    """Loads and clean the data from GAL and Sinan sources applying some filter rules."""

    def __init__(self):
        self.__datafolder = Path("dados/")
        if not self.__datafolder.exists():
            self.__datafolder.mkdir()
        self.df = None

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
                    logging.info(f"Dataset selecionado: {selected}")
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
        logging.info(
            "Identificando e removendo pacientes duplicados na base SINAN..."
        )
        logging.info(f"Total de linhas SINAN: {len(self.df_sin)}")

        DATE_COLUMN = "DT_SIN_PRI"

        # Define the criteria for identifying duplicates
        duplicate_criteria = ["NM_PACIENT", "DT_NASC", "NM_MAE_PAC"]
        MAX_NOTIFICATION_DATE_DIFF = pd.Timedelta(days=15)

        # Sort the SINAN dataset by notification date
        self.df_sin.sort_values(by=[DATE_COLUMN], inplace=True)

        # Find and mark duplicates based on the specified criteria
        duplicated_mask = self.df_sin.duplicated(
            subset=duplicate_criteria, keep=False
        )

        grouped = self.df_sin[duplicated_mask].groupby(duplicate_criteria)

        # Filter the duplicates based on the maximum notification date difference
        considered_patients_duplicates = []
        for group_name, group_index in grouped.groups.items():
            group = self.df_sin.loc[group_index]
            considered_patients = [group.iloc[0]]
            for _, patient in group.iloc[1:].iterrows():
                if (
                    abs(
                        considered_patients[-1][DATE_COLUMN]
                        - patient[DATE_COLUMN]
                    )
                    <= MAX_NOTIFICATION_DATE_DIFF
                ):
                    considered_patients.append(patient)
                else:
                    logging.warning(
                        f'Paciente {patient["NM_PACIENT"]} foi removido por duplicidade.'
                    )

            considered_patients_str = "\t\n".join(
                str(p["NM_PACIENT"]) for p in considered_patients
            )

            logging.debug(
                f"Grupo de Duplicados: {group_name} foram considerados:\n{considered_patients_str}"
            )
            considered_patients_duplicates.extend(considered_patients)

        df_considered_duplicates = pd.DataFrame(considered_patients_duplicates)
        df_non_duplicates = self.df_sin[~duplicated_mask]

        self.df_sin = pd.concat(
            [df_non_duplicates, df_considered_duplicates], ignore_index=True
        )
        self.df_sin.reset_index(drop=True, inplace=True)

        logging.info(
            f"Pacientes duplicados removidos. Total: {len(self.df_sin)}"
        )

    def __join_datasets(self):
        """
        Join datasets based on specified criteria and update the self.df attribute with the combined data.
        """
        logging.info("Juntando as bases GAL e SINAN...")

        DATE_SIN_COLUMN = "DT_SIN_PRI"
        DATE_GAL_COLUMN = "Data do 1º Sintomas"

        # Define the maximum notification date difference (1 week)
        max_notification_date_diff = pd.Timedelta(days=7)
        new_rows = []

        for _, row in self.df_sin.iterrows():
            results = self.df_gal[
                (self.df_gal["Paciente"] == row["NM_PACIENT"])
                & (self.df_gal["Data de Nascimento"] == row["DT_NASC"])
                & (self.df_gal["Nome da Mãe"] == row["NM_MAE_PAC"])
            ]
            to_extend = []
            for _, result in results.iterrows():
                # Check if the notification date is within the maximum notification date difference
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
        if self.df is None:
            raise Exception("Merged dataframe is not defined yet.")

        exams_map = {
            "Dengue, IgM": "IgM",
            "Dengue, Detecção de Antígeno NS1": "NS1",
            "Dengue, Biologia Molecular": "PCR",
            "Pesquisa de Arbovírus (ZDC)": "PCR",
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
                (row["Data do 1º Sintomas"] - row["Data da Coleta"])
            )

            return rule(elapsed_time)

        self.df = self.df[
            self.df.apply(filter_content, axis=1, result_type="reduce")
        ]
        logging.info(
            f"Total de pacientes hábeis para irem para o SINAN: {len(self.df)}"
        )

    def clean_data(self):
        """
        Method to clean the data. It logs the start of the cleaning process, loads the data, logs the successful data load, and then iterates through a list of cleaning functions to clean the data.
        """
        logging.info("Iniciando a limpeza dos dados...")

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

        normalize_columns(self.df_gal, ["Paciente", "Nome da Mãe"])
        to_datetime(
            self.df_gal,
            ["Data de Nascimento", "Data do 1º Sintomas", "Data da Coleta"],
            format="%d-%m-%Y",
        )

        # SINAN
        print("Escolha o dataset do SINAN para usar...")
        self.df_sin = self.__get_df()
        normalize_columns(self.df_sin, ["NM_PACIENT", "NM_MAE_PAC"])
        to_datetime(self.df_sin, ["DT_NASC", "DT_SIN_PRI"])
        self.clean_data()


class ConsultarNotificacao:
    """Consult a notification given a patient name

    Args:
        session (requests.Session): Requests session logged obj
        agravo (str): Agravo to filter by (eg. A90 - DENGUE)

    Methods:
        consultar(self, patient: str): Consult a notification and return the response
    """

    def __init__(
        self, session: requests.Session, agravo: Literal["A90 - DENGUE"]
    ):
        self.session = session
        self.base_payload = {
            "AJAXREQUEST": "_viewRoot",
            "form": "form",
            "form:consulta_tipoPeriodo": "0",
            "form:consulta_dataInicialInputDate": FIRST_YEAR_DAY.strftime(
                "%d/%m/%Y"
            ),
            "form:consulta_dataInicialInputCurrentDate": TODAY.strftime(
                "%m/%Y"
            ),
            "form:consulta_dataFinalInputDate": TODAY.strftime("%d/%m/%Y"),
            "form:consulta_dataFinalInputCurrentDate": TODAY.strftime("%m/%Y"),
            "form:richagravocomboboxField": agravo,
            "form:richagravo": agravo,
            "form:tipoUf": "3",  # Notificação ou Residência
            "form:consulta_uf": "24",  # SC
            "form:tipoSaida": "2",  # Lista de Notificação
            "form:consulta_tipoCampo": "0",
            "form:consulta_municipio_uf_id": "0",
            "form:j_id161": "Selecione valor no campo",
        }
        self.endpoint = (
            f"{BASE_URL}/sinan/secured/consultar/consultarNotificacao.jsf"
        )

    def __selecionar_agravo(self):
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:j_id108": "form:j_id108",
                "AJAX:EVENTS_COUNT": "1",
            }
        )
        self.session.post(self.endpoint, data=payload)

    def __adicionar_criterio(self):
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": "13",
                "form:consulta_operador": "2",
                "form:consulta_municipio_uf_id": "0",
                "form:consulta_dsTextoPesquisa": self.paciente,
                "form:btnAdicionarCriterio": "form:btnAdicionarCriterio",
            }
        )
        payload.pop("form:j_id161", None)
        self.session.post(self.endpoint, data=payload)

    def __selecionar_criterio_campo(self):
        CRITERIO = "Nome do paciente"

        options = self.soup.find("select", {"id": "form:consulta_tipoCampo"}).find_all("option")  # type: ignore
        tipo_campo = next(
            (option for option in options if option.text.strip() == CRITERIO),
            None,
        )

        if not tipo_campo:
            logging.error(f"Criterio {CRITERIO} not found.")
            exit(1)

        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": tipo_campo.get("value"),
                "form:j_id136": "form:j_id136",
                "ajaxSingle": "form:consulta_tipoCampo",
            }
        )
        self.session.post(self.endpoint, data=payload)

        self.__adicionar_criterio()

    def __pesquisar(self):
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:btnPesquisar": "form:btnPesquisar",
            }
        )
        res = self.session.post(self.endpoint, data=payload)
        return res

    def consultar(self, paciente: str):
        self.paciente = paciente

        res = self.session.get(self.endpoint)
        self.soup = BeautifulSoup(res.content, "html.parser")
        javax_faces = self.soup.find("input", {"name": "javax.faces.ViewState"})
        if not javax_faces or isinstance(javax_faces, NavigableString):
            logging.error("Java Faces not found.")
            exit(1)

        self.base_payload["javax.faces.ViewState"] = javax_faces.get("value")  # type: ignore

        self.__selecionar_agravo()
        self.__selecionar_criterio_campo()
        res = self.__pesquisar()
        return res


class Sinan:
    """Sinan client taht will be used to interact with the Sinan Website doing things like:
    - Login
    - Filling out forms
    - Verifying submitted forms
    """

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self.__init_apps()

    def _get_data(self):
        self.data = Data()
        self.data.load()

    def __create_session(self):
        self.session = requests.session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                )
            }
        )

    def __create_consultor(self):
        self.consultor = ConsultarNotificacao(self.session, "A90 - DENGUE")

    def __init_apps(self):
        apps = [self.__create_session, self.__create_consultor]

        for app in apps:
            app()

    def __verify_login(self, res: requests.Response):
        soup = BeautifulSoup(res.content, "html.parser")
        if not soup.find("div", {"id": "detalheUsuario"}):
            logging.error("Login failed.")
            exit(1)

    def _login(self):
        logging.info("Logando no SINAN...")
        self.__create_session()

        # set JSESSIONID
        res = self.session.get(f"{BASE_URL}/sinan/login/login.jsf")

        soup = BeautifulSoup(res.content, "html.parser")
        form = soup.find("form")
        if not form or isinstance(form, NavigableString):
            logging.error("Login Form not found.")
            exit(1)

        inputs = form.find_all("input")
        payload = dict()
        for input_ in inputs:
            name, value = input_.get("name"), input_.get("value")
            if "username" in name:
                value = self._username
            elif "password" in name:
                value = self._password
            payload[name] = value

        res = self.session.post(
            f"{BASE_URL}{form.get('action')}",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.__verify_login(res)
        logging.info("Logado com sucesso.")

    def __consult_patient(self, patient: str):
        self.consultor.consultar(patient)

    def fill(self):
        self._login()
        # for patient in patients: self.__consult_patient(patient) # TODO


if __name__ == "__main__":
    credentials_path = Path("credentials.json")
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

    sinan = Sinan(**credentials)
    sinan.fill()
