from datetime import datetime
from typing import Optional

import pandas as pd

from core.constants import (
    EXAM_RESULT_ID,
    EXAM_VALUE_COL_MAP,
    EXAMS_GAL_MAP,
    POSSIBLE_EXAM_TYPES,
)


class Properties:
    """Class to handle properties of patient data"""

    data: dict

    @property
    def exam_type(self) -> POSSIBLE_EXAM_TYPES:
        """Gets the exam type (IgM, NS1, PCR).

        Returns:
            POSSIBLE_EXAM_TYPES: The type of exam.
        """
        return EXAMS_GAL_MAP[self.data["Exame"]]

    @property
    def name(self) -> str:
        """Gets the patient name.

        Returns:
            str: The patient's name.
        """
        return self.data["Paciente"]

    @property
    def exam_result(self) -> str:
        """Gets the result of the exam.

        Returns:
            str: The result of the exam.
        """
        result_exam_col_name = EXAM_VALUE_COL_MAP[self.exam_type]
        return self.data[result_exam_col_name]

    @property
    def notification_number(self) -> str:
        """Gets the notification number given by the GAL.

        Returns:
            str: The notification number.
        """
        return self.data["Núm. Notificação Sinan"]

    @property
    def birth_date(self) -> Optional[datetime]:
        """Gets the birth date of the patient (object).

        Returns:
            Optional[datetime]: The birth date of the patient.
        """
        return (
            self.data["Data de Nascimento"]
            if not pd.isna(self.data["Data de Nascimento"])
            else None
        )

    @property
    def f_birth_date(self) -> str:
        """Gets the formatted birth date (dd/mm/YYYY).

        Returns:
            str: The formatted birth date or N/A.
        """
        return self.birth_date.strftime("%d/%m/%Y") if self.birth_date else "N/A"

    @property
    def mother_name(self) -> str:
        """Gets the mother's name.

        Returns:
            str: The mother's name.
        """
        return self.data["Nome da Mãe"]

    @property
    def notification_date(self) -> datetime:
        """Gets the notification date given by the GAL.

        Returns:
            datetime: The notification date.
        """
        return self.data["Data da Notificação"]

    @property
    def collection_date(self) -> datetime:
        """Gets the date of the collection (GAL - Exam).

        Returns:
            datetime: The collection date.
        """
        return self.data["Data da Coleta"]

    @property
    def f_collection_date(self) -> str:
        """Gets the formatted collection date (dd/mm/YYYY).

        Returns:
            str: The formatted collection date.
        """
        return self.collection_date.strftime("%d/%m/%Y")

    @property
    def exam_result_map(self):
        """Gets the exam result ID map.

        Returns:
            dict: The exam result ID map.
        """
        return EXAM_RESULT_ID[self.exam_type]

    @property
    def sinan_result_id(self):
        """Gets the SINAN result ID.

        Returns:
            str: The SINAN result ID.
        """
        return self.exam_result_map[self.exam_result]

    @property
    def sorotypes(self) -> list[str]:
        """Gets the sorotypes from the data.

        Returns:
            list[str]: The list of sorotypes.
        """
        sorotypes = self.data.get("Sorotipo", "")
        if pd.isna(sorotypes):
            return []
        return sorotypes.split(" e ")


class Patient(Properties):
    """Patient representation from GAL database.

    A lot of properties are defined here for easy access.

    Attributes:
        data (dict): The patient data.
    """

    def __init__(self, patient_data: dict):
        """Initializes the Patient with patient data.

        Args:
            patient_data (dict): The patient data.
        """
        self.data = patient_data
