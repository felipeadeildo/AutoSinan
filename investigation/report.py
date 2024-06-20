from datetime import datetime
from typing import Literal

import pandas as pd
from openpyxl.styles import Border, PatternFill, Side

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
            "Sorotipo",
            "Data da Coleta",
        ]
        self.df = pd.DataFrame(columns=self.columns)
        self.df = self.df[self.columns]

        self.__messages_stack = []
        self.__current_patient = {}

        self.__importance_map = {
            "debug": "Informação Simples",
            "info": "Informação de Progresso",
            "warn": "Aviso (Atenção)",
            "error": "Erro",
            "success": "Sucesso",
        }
        self.__importance_color_map = {
            "debug": "FFFFFF",  # White
            "info": "ADD8E6",  # Light Blue
            "warn": "FFFFE0",  # Light Yellow
            "error": "FFC0CB",  # Light Pink
            "success": "90EE90",  # Light Green
        }

        self.__reports_filename = None

        self.stats = {
            "total_patients": 0,
            "total_errors": 0,
            "total_notifications": 0,
            "total_duplicates": 0,
            "total_oportunity": 0,
            "total_non_oportunity": 0,
            "total_investigated": 0,
            "total_warns": 0,
            "average_search_time": 0,
            "average_fill_time": 0,
            "average_investigation_time": 0,
            "average_notifications_found": 0,
            "average_notification_attempts": 0,
        }

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
            "Sorotipo": "; ".join(patient.sorotypes) or "Nenhum Sorotipo Informado",
            "Data da Coleta": patient.f_collection_date,
        }

    def clean_patient(self):
        """Clean the current patient data"""
        self.__current_patient = {}

    def __apply_colors(self, worksheet):
        """Apply colors to cells in 'Categoria da Mensagem' column based on importance"""
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        for row_idx, category in enumerate(self.df["Categoria da Mensagem"], start=2):
            color = self.__importance_color_map.get(
                next(
                    k
                    for k in self.__importance_map
                    if self.__importance_map[k] == category
                ),
                "FFFFFF",
            )
            fill_pattern = PatternFill(
                start_color=color, end_color=color, fill_type="solid"
            )
            cell = worksheet[f"A{row_idx}"]
            cell.fill = fill_pattern
            cell.border = thin_border

    def __export(self):
        """Export the current dataframe to an excel file if the filename is defined"""
        if self.__reports_filename is None:
            return

        writer = pd.ExcelWriter(
            SCRIPT_GENERATED_PATH / self.__reports_filename, engine="openpyxl"
        )
        self.df.to_excel(writer, sheet_name="Relatório", index=False)

        worksheet = writer.sheets["Relatório"]

        for idx, col in enumerate(self.df.columns):
            max_len = max(self.df[col].astype(str).str.len().max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_len

        self.__apply_colors(worksheet)

        writer.close()

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
        importance: Literal["debug", "info", "warn", "error", "success"],
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

    def success(self, message: str, observation: str = ""):
        """Add a success message (Importance: Sucesso)

        Args:
            message (str): The message
            observation (str, optional): Some observation about the message. Defaults to "".
        """
        self.__add_message(message, "success", observation)

    def _example(self):
        """Just for testing purposes"""
        self.debug("Alguma coisa que o bot fez, e geralmente pode ser ignorado.")
        self.info(
            "Alguma decisão que o bot tomou, não atrapalha em nada, mas é bom saber que ele tomou tal decisão"
        )
        self.warn(
            "Alguma decisão que que o bot tomou mais 'severas', como 'exclui' uma ficha ou indicar que alguma coisa não foi feita por algum motivo"
        )
        self.error(
            "Algum erro e que precisa ser revisado, algo que impediu de alguma forma, por algum motivo, que a ficha fosse investigada"
        )
        self.success("Indicador claro e objetivo que a ficha foi investigada")
