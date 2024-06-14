from datetime import datetime

import pandas as pd

from core.constants import (
    EXAM_RESULT_ID,
    EXAM_VALUE_COL_MAP,
    EXAMS_GAL_MAP,
    POSSIBLE_EXAM_TYPES,
)


class Properties:
    data: dict

    @property
    def exam_type(self) -> POSSIBLE_EXAM_TYPES:
        """Exam type (IgM, NS1, PCR)"""
        return EXAMS_GAL_MAP[self.data["Exame"]]

    @property
    def name(self) -> str:
        """Patient name"""
        return self.data["Paciente"]

    @property
    def exam_result(self) -> str:
        """Result of the exam"""
        result_exam_col_name = EXAM_VALUE_COL_MAP[self.exam_type]
        return self.data[result_exam_col_name]

    @property
    def notification_number(self) -> str:
        """Notification number given by the GAL"""
        return self.data["Núm. Notificação Sinan"]

    @property
    def birth_date(self) -> datetime:
        """Birth date of the patient (object)"""
        return self.data["Data de Nascimento"]

    @property
    def f_birth_date(self):
        """Formatted birth date (dd/mm/YYYY)"""
        return self.birth_date.strftime("%d/%m/%Y")

    @property
    def mother_name(self) -> str:
        """Mother name"""
        return self.data["Nome da Mãe"]

    @property
    def notification_date(self) -> datetime:
        """Notification date given by the GAL"""
        return self.data["Data da Notificação"]

    @property
    def collection_date(self) -> datetime:
        """Date of the Collect (GAL - Exam)"""
        return self.data["Data da Coleta"]

    @property
    def f_collection_date(self) -> str:
        """Formatted collection date (dd/mm/YYYY)"""
        return self.collection_date.strftime("%d/%m/%Y")

    @property
    def exam_result_map(self):
        return EXAM_RESULT_ID[self.exam_type]

    @property
    def sinan_result_id(self):
        return self.exam_result_map[self.exam_result]

    @property
    def sorotypes(self) -> list[str]:
        sorotypes = self.data.get("Sorotipo", "")
        if pd.isna(sorotypes):
            return []
        return sorotypes.split(" e ")


class Patient(Properties):
    """Patient representation from GAL database

    A lot of properties are defined here for easy access.
    """

    def __init__(self, patient_data: dict):
        self.data = patient_data
