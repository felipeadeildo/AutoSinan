import requests
from bs4 import BeautifulSoup

from core.constants import SINAN_BASE_URL
from core.utils import valid_tag


class Investigator:
    """Given a patient data and your payload to open the Sinan page, this class will be used to investigate the patient."""

    def __init__(self, session: requests.Session) -> None:
        self.session = session
        self.open_investigation_endpoint = (
            f"{SINAN_BASE_URL}/sinan/secured/consultar/consultarNotificacao.jsf"
        )

    def investigate(
        self,
        patient_data: dict,
        sinan_response: dict,
    ):
        # the most efficient debug, lol
        print("arrived here:", patient_data, sinan_response)
        response = self.session.post(
            self.open_investigation_endpoint,
            data=sinan_response["open_payload"],
        )
        self.soup = BeautifulSoup(response.content, "html.parser")

        if not valid_tag(
            self.soup.find(attrs={"id": "form:tabInvestigacao_lbl"})
        ):
            # deve-se marcar como “Não” obrigatoriamente desprezando o que tiver na BASE unificada nos campos 34 e 33
            # clicar em "salvar" e em "ok"
            ...
