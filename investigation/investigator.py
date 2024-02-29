import json
import re
from typing import Mapping, Optional

import requests
from bs4 import BeautifulSoup

from core.constants import (
    CLASSSIFICATION_MAP,
    EXAM_RESULT_ID,
    EXAM_VALUE_COL_MAP,
    EXAMS_GAL_MAP,
    POSSIBLE_EXAM_TYPES,
    SINAN_BASE_URL,
    TODAY,
)
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

    def __submit_modal_ok(self):
        """Click in "Ok" buttom if modal appears in the response"""

        show_modal_script = next(
            (
                s
                for s in self.soup.find_all("script")
                if s.text.strip().endswith(".component.show();")
            ),
            None,
        )
        if not show_modal_script:
            print("Script to show modal not found.")
            return

        show_modal_text = "".join(show_modal_script.text.split("\n")).strip()

        modal_id_match = re.search(
            r"getElementById\(['\"]([^'\"]+)['\"]\)", show_modal_text
        )
        if not modal_id_match:
            print("Error: Modal id not found")
            raise ValueError("Modal id not found")

        modal_id = modal_id_match.group(1)
        payload_modal_ok = self.__get_form_data("div", {"id": modal_id})
        payload_modal_ok = {
            k: v for k, v in payload_modal_ok.items() if "ok" in v.lower()
        }
        self.current_form.pop("form:botaoSalvar", None)

        response = self.session.post(
            self.notification_endpoint,
            data={**self.current_form, **payload_modal_ok},
        )

        self.soup = BeautifulSoup(response.content, "html.parser")

    def __enable_and_open_investigation(self):
        """Enable the investigation aba and open it (the response form)

        Args:
            form_data (dict): The patient form data to open investigation
        """
        self.current_form = {
            k: v
            for k, v in self.current_form.items()
            if k
            and not k.startswith(
                (
                    "form:j_id",
                    "form:btn",
                )
            )
        }
        self.current_form.update(
            {
                "form:richagravo": self.current_form[
                    "form:richagravocomboboxField"
                ],
            }
        )
        response = self.session.post(
            self.notification_endpoint, data=self.current_form
        )
        self.soup = BeautifulSoup(response.content, "html.parser")

        first_investigation_input = valid_tag(
            self.soup.find(
                "input", attrs={"id": "form:dtInvestigacaoInputDate"}
            )
        )
        # when there is no investigation form, so probabilly exists a modal being shown
        if not first_investigation_input:
            try:
                self.__submit_modal_ok()
            except ValueError:
                # TODO: handle modal not found
                pass

    def __define_exam_result_data(self):
        """Get the payload with the exam result which is one of the options in the Sinan Investigation Form and fill the exam result.

        Possible Inputs that can be filled:
            39, 41, 45 - Data da Coleta,
            40, 42, 46 - Resultado,
            47 - Sorotipo
        """
        exam_type = EXAMS_GAL_MAP[self.patient_data["Exame"]]
        exam_result_map = EXAM_RESULT_ID[exam_type]
        formatted_collection_date = self.patient_data[
            "Data da Coleta"
        ].strftime("%d/%m/%Y")

        if exam_type == "PCR":
            patient_data_result_column = EXAM_VALUE_COL_MAP[exam_type]
            payload_collection_date_column = (
                "form:dengue_dataColetaRTPCRInputDate"
            )
            payload_collection_result_column = "form:dengue_resultadoRTPCR"
            exam_result = str(self.patient_data[patient_data_result_column])
            payload_exam_result = exam_result_map.get(
                exam_result, exam_result_map["_default"]
            )

            # select the sorotype
            self.current_form.update(
                {
                    payload_collection_date_column: formatted_collection_date,
                    payload_collection_result_column: payload_exam_result,
                }
            )
            # allow the "47 - sorotipo" to be selected
            self.session.post(
                self.notification_endpoint,
                data={**self.current_form, "form:j_id572": "form:j_id572"},
            )

            if payload_exam_result == "1":
                sorotype_dengue = self.current_form["Sorotipo"].removeprefix(
                    "DENV"
                )  # DENV1, DENV2, etc
                self.current_form.update(
                    {
                        "form:dengue_sorotipo": sorotype_dengue,
                    }
                )
                # save the sorotype
                self.session.post(
                    self.notification_endpoint,
                    data={
                        **self.current_form,
                        "form:j_id577": "form:j_id577",
                    },
                )

        elif exam_type == "IgM":
            patient_data_result_column = EXAM_VALUE_COL_MAP[exam_type]
            payload_collection_date_column = (
                "form:dengue_dataColetaExameSorologicoInputDate"
            )
            payload_collection_result_column = (
                "form:dengue_resultadoExameSorologico"
            )
            exam_result = str(self.patient_data[patient_data_result_column])
            payload_exam_result = exam_result_map.get(exam_result)

            if not payload_exam_result:
                raise Exception(
                    "Não foi possível definir o resultado do exame."
                )

            self.current_form.update(
                {
                    payload_collection_date_column: formatted_collection_date,
                    payload_collection_result_column: payload_exam_result,
                }
            )

        elif exam_type == "NS1":
            patient_data_result_column = EXAM_VALUE_COL_MAP[exam_type]
            payload_collection_date_column = (
                "form:dengue_dataColetaNS1InputDate"
            )
            payload_collection_result_column = "form:dengue_resultadoNS1"
            exam_result = self.patient_data[patient_data_result_column]
            payload_exam_result = exam_result_map[exam_result]
            self.current_form.update(
                {
                    payload_collection_date_column: formatted_collection_date,
                    payload_collection_result_column: payload_exam_result,
                }
            )

    def __select_classification(self):
        """Select the classification based on the exam results (62 - Classificação)"""
        if self.current_form["form:dengue_classificacao"] in ("11", "12"):
            return

        exam_results: Mapping[POSSIBLE_EXAM_TYPES, str | None] = {
            "IgM": self.current_form["form:dengue_resultadoExameSorologico"],
            "NS1": self.current_form["form:dengue_resultadoNS1"],
            "PCR": self.current_form["form:dengue_resultadoRTPCR"],
        }

        classifications = []
        for exam_type, result in exam_results.items():
            possible_classifications = CLASSSIFICATION_MAP[exam_type]
            possible_exam_results = EXAM_RESULT_ID[exam_type]
            classification_key = next(
                (k for k, v in possible_exam_results.items() if v == result),
                None,
            )
            if not classification_key:
                continue
            classification = possible_classifications[classification_key]
            classifications.append(classification)

        if any(map(lambda k: k == "10", classifications)):
            self.current_form.update({"form:dengue_classificacao": "10"})
        elif any(map(lambda k: k == "5", classifications)):
            self.current_form.update({"form:dengue_classificacao": "5"})
        self.session.post(
            self.notification_endpoint,
            data={**self.current_form, "form:j_id713": "form:j_id713"},
        )

    def __select_criteria(self):
        """Select the confirmation criteria (63 - Critério de Confirmação)"""
        self.current_form.update({"form:dengue_criterio": "1"})
        self.session.post(
            self.notification_endpoint,
            data={**self.current_form, "form:j_id718": "form:j_id718"},
        )

    def __define_closing_date(self):
        """Insert the value of the closing date (67 - Data de Encerramento)"""
        if self.current_form["form:dengue_dataEncerramentoInputDate"]:
            return
        elif self.current_form["form:dengue_classificacao"] in ("11", "12"):
            return

        self.current_form.update(
            {
                "form:dengue_dataEncerramentoInputDate": TODAY.strftime(
                    "%d/%m/%Y"
                )
            }
        )
        self.session.post(
            self.notification_endpoint,
            data={**self.current_form, "form:j_id739": "form:j_id739"},
        )

    def __define_investigation_date(self):
        """Define the investigation date (31 - Data da Investigação)"""
        self.current_form.update(
            {"form:dtInvestigacaoInputDate": TODAY.strftime("%d/%m/%Y")}
        )
        self.session.post(
            self.notification_endpoint,
            data={**self.current_form, "form:j_id402": "form:j_id402"},
        )

    def __select_clinical_signs(self):
        """Select the clinical signs (33 - Sinais Clinicos)"""
        self.current_form.update(
            {
                k: (
                    (v or "2")
                    if not self.force_clinal_signs_and_illnesses
                    else "2"
                )
                for k, v in self.current_form.items()
                if k.startswith("form:chikungunya_sinais")
            }
        )

    def __select_illnesses(self):
        """Select the illnesses (34 - Doencas Pré-existentes)"""
        self.current_form.update(
            {
                k: (
                    (v or "2")
                    if not self.force_clinal_signs_and_illnesses
                    else "2"
                )
                for k, v in self.current_form.items()
                if k.startswith("form:chikungunya_doencas")
            }
        )

    def __save_investigation(self):
        """Save the Investigation filled form date and submit it."""
        self.current_form.update(
            {"form:btnSalvarInvestigacao": "form:btnSalvarInvestigacao"}
        )
        response = self.session.post(
            self.notification_endpoint, data=self.current_form
        )
        with open("response.html", "wb") as f:
            f.write(response.content)

    def __fill_patient_data(self):
        self.current_form = {
            "AJAXREQUEST": "_viewRoot",
            "form": "form",
            "form:dengue_obeservacoes": "",
            "form:modalNotificacaoComInvestigacaoOpenedState": "",
            "javax.faces.ViewState": self._javax_view_state,
        }

        self.current_form.update(
            self.__get_form_data(attrs={"id": "form:tabPanelNotificacao"})
        )

        self.current_form = {
            k: v
            for k, v in self.current_form.items()
            if not k.startswith(("form:j_id8", "form:btn"))
        }

        factory_form_builders = [
            self.__define_exam_result_data,
            self.__define_investigation_date,
            self.__select_classification,
            self.__select_criteria,
            self.__define_closing_date,
            self.__select_clinical_signs,
            self.__select_illnesses,
        ]

        for builder in factory_form_builders:
            builder()

        # print(json.dumps(self.current_form, indent=4))
        self.__save_investigation()

    def __get_javafaces_view_state(self):
        """Get the javax.faces.ViewState tag from the current page"""
        self._javax_view_state = valid_tag(
            self.soup.find(attrs={"name": "javax.faces.ViewState"})
        )

        if not self._javax_view_state:
            print("Não foi possível obter o javax.faces.ViewState.")
            return

        self._javax_view_state = self._javax_view_state.get("value")

    def __open_investigation_page(self, sinan_response: dict):
        """Open the investigation page

        Args:
            sinan_response (dict): The payload to open the investigation (from the Sinan Researcher class)
        """
        response = self.session.post(
            self.open_investigation_endpoint,
            data=sinan_response["open_payload"],
        )
        self.soup = BeautifulSoup(response.content, "html.parser")
        self.__get_javafaces_view_state()

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
        self.patient_data = patient_data
        self.__open_investigation_page(sinan_response)

        self.current_form = self.__get_form_data()

        navigation_tag = valid_tag(
            self.soup.find(attrs={"id": "form:tabInvestigacao_lbl"})
        )
        if not navigation_tag:
            print("Erro: A tag de navegação não foi encontrada.")
            return

        # verify if the investigation tab is enabled
        self.force_clinal_signs_and_illnesses = "rich-tab-disabled" in (
            navigation_tag.get("class") or []
        )

        self.__enable_and_open_investigation()
        self.__fill_patient_data()
