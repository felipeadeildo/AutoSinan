from typing import List

import requests

from investigation.patient import Patient
from investigation.report import Report
from investigation.sheet import Sheet


class NotFoundError(Exception):
    """Raised when something in the page was not found."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DuplicateChecker:
    """Given a patient data and your payload to open the Sinan page, this class will be used to investigate the patient."""

    def __init__(self, session: requests.Session, reporter: Report) -> None:
        self.session = session
        self.reporter = reporter

    def investigate_multiple(self, patient: Patient, sheets: List[Sheet]):
        """Investigate multiple patients filling out the patient data on the Sinan Investigation page

        Args:
            patient (Patient): The patient to be investigated
            sheets (List[Sheet]): The list of sheets to be duplicity-analyzed
        """
        # TODO: implement this
        self.reporter.error("Análise de duplicidades ainda não foi implementado.")
