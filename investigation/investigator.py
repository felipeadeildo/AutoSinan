import json
from typing import Optional

import requests
from bs4 import BeautifulSoup

from core.constants import EXAMS_GAL_MAP, SINAN_BASE_URL
from core.utils import valid_tag


class Investigator:
    """Given a patient data and your payload to open the Sinan page, this class will be used to investigate the patient."""

    def __init__(self, session: requests.Session) -> None:
        self.session = session
        self.open_investigation_endpoint = (
            f"{SINAN_BASE_URL}/sinan/secured/consultar/consultarNotificacao.jsf"
        )
        self.notification_endpoint = f"{SINAN_BASE_URL}/sinan/secured/notificacao/individual/dengue/dengueIndividual.jsf"

    def __get_form_data(
        self, tag_name: Optional[str] = None, attrs: dict = {"id": "form"}
    ) -> dict:
        """Return the default values of the form fields

        Args:
            tag_name (str, optional): BeautifulSoup tag name. Defaults to `form`.
            attrs (dict, optional): BeautifulSoup tag attributes. Defaults to `{"id": "form"}`
                Example: `attrs={"id": "form:j_id"}`

        Returns:
            dict: A dictionary with the form default data
        """
        form = valid_tag(self.soup.find(tag_name, attrs=attrs))

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

    def __get_payload_exam_result(
        self, patient_data: dict, current_payload: dict
    ) -> Optional[dict]:
        exam_type = EXAMS_GAL_MAP[patient_data["Exame"]]
        local_payload = current_payload.copy()
        formatted_collection_date = patient_data["Data da Coleta"].strftime(
            "%d/%m/%Y"
        )
        match exam_type:
            case "PCR":
                patient_data_result_column = "Dengue"
                payload_collection_date_column = (
                    "form:dengue_dataColetaRTPCRInputDate"
                )
                payload_collection_result_column = "form:dengue_resultadoRTPCR"
                exam_result = str(patient_data[patient_data_result_column])
                exam_result_map = {
                    "Não Detectável": "2",  # Negativo
                    "Detectável": "1",  # Positivo
                    "_default": "3",  # Inconclusivo
                }
                payload_exam_result = exam_result_map.get(
                    exam_result, exam_result_map["_default"]
                )

                # select the sorotype
                local_payload.update(
                    {
                        payload_collection_date_column: formatted_collection_date,
                        payload_collection_result_column: payload_exam_result,
                        "form:j_id572": "form:j_id572",
                    }
                )
                # allow the "47 - sorotipo" to be selected
                self.session.post(
                    self.notification_endpoint, data=local_payload
                )
                local_payload.pop("form:j_id572")

                if payload_exam_result == "1":
                    sorotype_dengue = patient_data["Sorotipo"].removeprefix(
                        "DENV"
                    )  # DENV1, DENV2, etc
                    local_payload.update(
                        {
                            "form:dengue_sorotipo": sorotype_dengue,
                            "form:j_id577": "form:j_id577",
                        }
                    )
                    # save the sorotype
                    self.session.post(
                        self.notification_endpoint, data=local_payload
                    )
                    local_payload.pop("form:j_id577")

            case "IgM":
                patient_data_result_column = "Resultado"
                payload_collection_date_column = (
                    "form:dengue_dataColetaExameSorologicoInputDate"
                )
                payload_collection_result_column = (
                    "form:dengue_resultadoExameSorologico"
                )
                exam_result = str(patient_data[patient_data_result_column])
                exam_result_map = {
                    "Não Reagente": "2",  # Não Reagente
                    "Reagente": "1",  # Reagente
                    "Indeterminado": "3",  # Inconclusivo
                }
                payload_exam_result = exam_result_map.get(exam_result)
                if not payload_exam_result:
                    return print(
                        "Não foi possível definir o resultado do exame."
                    )

                local_payload.update(
                    {
                        payload_collection_date_column: formatted_collection_date,
                        payload_collection_result_column: payload_exam_result,
                    }
                )
            case "NS1":
                patient_data_result_column = "Resultado"
                payload_collection_date_column = (
                    "form:dengue_dataColetaNS1InputDate"
                )
                patient_data_result_column = "form:dengue_resultadoNS1"
                exam_result = patient_data[patient_data_result_column]
                exam_result_map = {
                    "Reagente": "1",  # Positivo
                    "Não Reagente": "2",  # Negativo
                    "Indeterminado": "3",  # Inconclusivo
                }
                payload_exam_result = exam_result_map[exam_result]
                local_payload.update(
                    {
                        payload_collection_date_column: formatted_collection_date,
                        patient_data_result_column: payload_exam_result,
                    }
                )

        return local_payload

    def __fill_patient_data(self, patient_data: dict):
        payload_base = {
            "AJAXREQUEST": "_viewRoot",
            "form": "form",
            "form:dengue_obeservacoes": "",
            "form:modalNotificacaoComInvestigacaoOpenedState": "",
            "javax.faces.ViewState": self._javax_view_state,
        }

        payload_base.update(
            self.__get_form_data(attrs={"id": "form:tabPanelNotificacao"})
        )

        payload_base = {
            k: v
            for k, v in payload_base.items()
            if not k.startswith(("form:j_id8", "form:btn"))
        }

        payload_exam_result = self.__get_payload_exam_result(
            patient_data, payload_base
        )
        if not payload_exam_result:
            return
        payload_base.update(payload_exam_result)
        # dev::verificate:
        print(json.dumps(payload_base, indent=4))

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
        self._javax_view_state = valid_tag(
            self.soup.find(attrs={"name": "javax.faces.ViewState"})
        )
        if not self._javax_view_state:
            print("Não foi possível obter o javax.faces.ViewState.")
            return
        self._javax_view_state = self._javax_view_state.get("value")

        form_data = self.__get_form_data()

        navigation_tag = valid_tag(
            self.soup.find(attrs={"id": "form:tabInvestigacao_lbl"})
        )
        if not navigation_tag:
            print("Erro: A tag de navegação não foi encontrada.")
            return

        if "rich-tab-disabled" in (navigation_tag.get("class") or []):
            # TODO: deve-se marcar como “Não” obrigatoriamente desprezando o que tiver na BASE unificada nos campos 34 e 33
            print("Aba de investigação tem que ser desbloqueada.")
            self.__enable_and_open_investigation(form_data)
        else:
            self.__enable_and_open_investigation(form_data)

        self.__fill_patient_data(patient_data)
