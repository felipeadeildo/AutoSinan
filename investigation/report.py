from datetime import datetime
from typing import Literal

import pandas as pd

from core.constants import EXAMS_GAL_MAP, EXECUTION_DATE, SCRIPT_GENERATED_PATH
from investigation.patient import Patient


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
            "Categoria da Mensagem",
            "Observações",
            "Data e Hora da Mensagem",
        ]
        self.df = pd.DataFrame(columns=self.columns)
        self.df = self.df[self.columns]

        # TODO: Add a chunk cleaner for this message stack and save the indice of the last chunk in self.df
        self.__messages_stack = []
        self.__current_patient = {}

        self.__importance_map = {
            "debug": "Informação Simples",
            "info": "Informação de Progresso",
            "warn": "Aviso (Atenção)",
            "error": "Erro",
        }
        self.__reports_filename = None

        # TODO: Implements a serie os stats using this controller that will be to generate a lot of stats on the end of the investigation
        self.stats = {}

    def set_patient(self, patient: Patient):
        """Set the current patient that the report will be about

        Args:
            patient (dict): The patient data from GAL
        """
        exam_type = patient.exam_type
        self.__current_patient = {
            "Nº de Notificação (GAL)": patient.notification_number,
            "Nome do Paciente": patient.name,
            "Nome da Mãe": patient.mother_name,
            "Data de Nascimento": patient.f_birth_date,
            "Tipo de Exame": exam_type,
            "Resultado do Exame": patient.exam_result,
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
        max_release_date = data["Data da Liberação"].max().strftime("%d.%m.%Y")
        min_release_date = data["Data da Liberação"].min().strftime("%d.%m.%Y")

        if max_release_date != min_release_date:
            release_dates = f"{min_release_date} à {max_release_date}"
        else:
            release_dates = max_release_date

        exams = ", ".join(map(lambda e: EXAMS_GAL_MAP[e], data["Exame"].unique()))
        run_datetime = EXECUTION_DATE.strftime("%d.%m.%Y às %Hh%M")
        self.__reports_filename = f"Investigação ({exams}) - liberação {release_dates} - execução {run_datetime}.xlsx"
        print(f"[RELATORIO] Nome do relatório: {self.__reports_filename}")
        self.__export()

    def __add_message(
        self,
        message: str,
        importance: Literal["debug", "info", "warn", "error"],
        observation: str = "",
    ):
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
                "Categoria da Mensagem": self.__importance_map[importance],
                "Observações": observation.strip(),
                "Data e Hora da Mensagem": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
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
        self.__add_message(message, "debug", observation)

    def info(self, message: str, observation: str = ""):
        """Add an info message (Importance: Informação de Progresso)

        Args:
            message (str): The message
            observation (str, optional): Some observation about the message. Defaults to "".
        """
        self.__add_message(message, "info", observation)

    def warn(self, message: str, observation: str = ""):
        """Add a warning message (Importance: Aviso (Atenção))

        Args:
            message (str): The message
            observation (str, optional): Some observation about the message. Defaults to "".
        """
        self.__add_message(message, "warn", observation)

    def error(self, message: str, observation: str = ""):
        """Add an error message (Importance: Erro)

        Args:
            message (str): The message
            observation (str, optional): Some observation about the message. Defaults to "".
        """
        self.__add_message(message, "error", observation)
