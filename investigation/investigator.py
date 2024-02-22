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
        self.notification_endpoint = f"{SINAN_BASE_URL}/sinan/secured/notificacao/individual/dengue/dengueIndividual.jsf"

    def __get_form_data(self, attrs: dict = {"id": "form"}) -> dict:
        """Return the default values of the form fields

        Args:
            attrs (dict, optional): BeautifulSoup tag attributes. Defaults to `{"id": "form"}`
                Example: `attrs={"id": "form:j_id"}`

        Returns:
            dict: A dictionary with the form default data
        """
        form = valid_tag(self.soup.find("form", attrs=attrs))

        if not form:
            print("Form not found.")
            exit(1)

        # for each input, get the name and value
        inputs = {
            i.get("name", ""): i.get("value", "")
            for i in form.find_all("input")
        }

        # for each select, get the name and selected option
        selects = {
            s.get("name", ""): next(
                (
                    opt.get("value")
                    for opt in s.find_all("option")
                    if opt.get("selected") == "selected"
                ),
                "",
            )
            for s in form.find_all("select")
        }

        return {**inputs, **selects}

    def __enable_and_open_investigation(self, form_data: dict):
        """Enable the investigation aba and open it (the response form)

        Args:
            form_data (dict): The patient form data to open investigation
        """
        payload = {
            k: v
            for k, v in form_data.items()
            if k
            and not k.startswith(
                (
                    "form:j_id",
                    "form:btn",
                )
            )
        }
        payload.update(
            {
                "form:richagravo": payload["form:richagravocomboboxField"],
            }
        )
        response = self.session.post(self.notification_endpoint, data=payload)
        self.soup = BeautifulSoup(response.content, "html.parser")

    def __fill_patient_data(self, patient_data: dict): ...

    def investigate(
        self,
        patient_data: dict,
        sinan_response: dict,
    ):
        """Investigate an patient filling out the patient data on the Sinan Investigation page

        Args:
            patient_data (dict): The patient date came from the data loader (SINAN + GAL datasets)
            sinan_response (dict): The payload to open the investigation (from the Sinan Researcher class)
        """
        response = self.session.post(
            self.open_investigation_endpoint,
            data=sinan_response["open_payload"],
        )
        self.soup = BeautifulSoup(response.content, "html.parser")

        form_data = self.__get_form_data()

        if not valid_tag(
            self.soup.find(attrs={"id": "form:tabInvestigacao_lbl"})
        ):
            # TODO: deve-se marcar como “Não” obrigatoriamente desprezando o que tiver na BASE unificada nos campos 34 e 33
            self.__enable_and_open_investigation(form_data)

        self.__fill_patient_data(patient_data)
