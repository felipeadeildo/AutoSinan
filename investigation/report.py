from datetime import datetime

import pandas as pd

from core.constants import (
    EXAM_VALUE_COL_MAP,
    EXAMS_GAL_MAP,
    EXECUTION_DATE,
    SCRIPT_GENERATED_PATH,
)


class Report:
    """The Report Generator to friendly-read investigation progress"""

    def __init__(self):
        self.columns = [
            "Nº de Notificação (GAL)",
            "Nome do Paciente",
            "Nome da Mãe",
            "Data de Nascimento",
            "Tipo de Exame",
            "Resultado do Exame",
            "Mensagem",
            "Importância da Mensagem",
            "Observações",
            "Data e Hora",
        ]
        self.df = pd.DataFrame(columns=self.columns)
        self.df = self.df[self.columns]

        # TODO: Add a chunk cleaner for this message stack and save the indice of the last chunk in self.df
        self.__messages_stack = []
        self.__current_patient = {}
        self.__importance_map = [
            "Informação Simples",
            "Informação de Progresso",
            "Aviso (Atenção)",
            "Erro",
        ]
        self.__reports_filename = None

    def set_patient(self, patient: dict):
        """Set the current patient that the report will be about

        Args:
            patient (dict): The patient data from GAL
        """
        exam_type = EXAMS_GAL_MAP[patient["Exame"]]
        result_exam_col_name = EXAM_VALUE_COL_MAP[exam_type]
        self.__current_patient = {
            "Nº de Notificação (GAL)": patient["Núm. Notificação Sinan"],
            "Nome do Paciente": patient["Paciente"],
            "Nome da Mãe": patient["Nome da Mãe"],
            "Data de Nascimento": patient["Data de Nascimento"].strftime("%d/%m/%Y"),
            "Tipo de Exame": exam_type,
            "Resultado do Exame": patient[result_exam_col_name],
        }

    def clean_patient(self):
        """Clean the current patient data"""
        self.__current_patient = {}

    def __export(self):
        """Export the current dataframe to an excel file if the filename is defined"""
        if self.__reports_filename is not None:
            self.df.to_excel(
                SCRIPT_GENERATED_PATH / self.__reports_filename, index=False
            )

    def generate_reports_filename(self, data: pd.DataFrame):
        """Generate the reports filename based on the date and the time of execution and release

        Args:
            data (pd.DataFrame): The GAL database
        """
        release_date = datetime.strptime(
            input("[DADOS] Data de liberação (dd/mm/aaaa): "), "%d/%m/%Y"
        )
        exams = ", ".join(map(lambda e: EXAMS_GAL_MAP[e], data["Exame"].unique()))
        run_datetime = EXECUTION_DATE.strftime("%d.%m.%Y %H-%M")
        self.__reports_filename = f"Investigação ({exams}) - liberação {release_date.strftime('%d.%m.%Y')} - execução {run_datetime}.xlsx"
        self.__export()

    def __add_message(self, message: str, importance: int = 0, observation: str = ""):
        """Low level function to add a message to the report

        Args:
            message (str): The message
            importance (int, optional): The message importance mapped. Defaults to 0.
            observation (str, optional): Some observation about the message. Defaults to "".
        """
        row = self.__current_patient.copy()
        if row.get("Nome do Paciente") is None:
            observation = (
                f"{observation} (Esta é uma mensagem sem relação à algum paciente)"
            )

        row.update(
            {
                "Mensagem": message,
                "Importância da Mensagem": self.__importance_map[importance],
                "Observações": observation.strip(),
                "Data e Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            }
        )

        self.__messages_stack.append(row)
        self.df = pd.DataFrame(self.__messages_stack)

        self.__export()

    def debug(self, message: str, observation: str = ""):
        """Add a debug message (Importance: Informação Simples)

        Args:
            message (str): The message
            observation (str, optional): Some observation about the message. Defaults to "".
        """
        self.__add_message(message, 0, observation)

    def info(self, message: str, observation: str = ""):
        """Add an info message (Importance: Informação de Progresso)

        Args:
            message (str): The message
            observation (str, optional): Some observation about the message. Defaults to "".
        """
        self.__add_message(message, 0, observation)

    def warn(self, message: str, observation: str = ""):
        """Add a warning message (Importance: Aviso (Atenção))

        Args:
            message (str): The message
            observation (str, optional): Some observation about the message. Defaults to "".
        """
        self.__add_message(message, 1, observation)

    def error(self, message: str, observation: str = ""):
        """Add an error message (Importance: Erro)

        Args:
            message (str): The message
            observation (str, optional): Some observation about the message. Defaults to "".
        """
        self.__add_message(message, 3, observation)
