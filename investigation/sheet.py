import re
from datetime import datetime, timedelta
from typing import Literal, Mapping

from bs4 import BeautifulSoup
from requests import Session

from core.constants import (
    CLASSIFICATION_FRIENDLY_MAP,
    CLASSSIFICATION_MAP,
    EXAM_RESULT_ID,
    POSSIBLE_EXAM_TYPES,
    PRIORITY_CLASSIFICATION_MAP,
    SINAN_BASE_URL,
    TODAY,
    TODAY_FORMATTED,
)
from core.utils import get_form_data, valid_tag
from investigation.patient import Patient
from investigation.report import Report

POSSIBLE_POSITIONS = Literal["results", "notification", "investigation"]


class Properties:
    """Properties of the sheet"""

    notification_soup: BeautifulSoup
    notification_form_data: dict
    investigation_soup: BeautifulSoup
    investigation_form_data: dict

    @property
    def first_symptoms_date(self) -> datetime:
        """Date of the first symptoms (object)"""
        return datetime.strptime(
            self.notification_form_data["form:dtPrimeirosSintomasInputDate"], "%d/%m/%Y"
        )

    @property
    def f_first_symptoms_date(self) -> str:
        """Formatted date of the first symptoms (dd/mm/YYYY)"""
        return self.first_symptoms_date.strftime("%d/%m/%Y")

    @property
    def is_investigation_sheet_enabled(self) -> bool:
        """Check if the investigation tab is enabled"""
        investigation_tab = valid_tag(
            self.notification_soup.find(attrs={"id": "form:tabInvestigacao_lbl"})
        )

        if not investigation_tab:
            print("[NOTIFICAÇÃO] Erro: Aba de investigação não foi encontrada.")
            raise FileNotFoundError

        return "rich-tab-disabled" not in (investigation_tab.get("class") or [])

    @property
    def javax_view_state(self) -> str:
        """Get the `javax.faces.ViewState` from the `notification_soup`"""
        tag = valid_tag(
            self.notification_soup.find(attrs={"name": "javax.faces.ViewState"})
        )

        if not tag:
            raise FileNotFoundError("Não foi possível obter o token de visualização.")

        return str(tag.get("value"))

    @property
    def dengue_classification(self) -> str:
        return self.investigation_form_data["form:dengue_classificacao"]

    @property
    def f_dengue_classification(self):
        return CLASSIFICATION_FRIENDLY_MAP[self.dengue_classification]

    @property
    def exam_results(self) -> Mapping[POSSIBLE_EXAM_TYPES, str | None]:
        return {
            "IgM": self.investigation_form_data["form:dengue_resultadoExameSorologico"],
            "NS1": self.investigation_form_data["form:dengue_resultadoNS1"],
            "PCR": self.investigation_form_data["form:dengue_resultadoRTPCR"],
        }

    @property
    def classifications(self):
        """List of classifications on Sinan based on the exam results (it doenst include the 11 and 12 classification because its defined by a human.)"""
        classifications = []
        for exam_type, result in self.exam_results.items():
            possible_classifications = CLASSSIFICATION_MAP[exam_type]
            possible_exam_results = EXAM_RESULT_ID[exam_type]
            classification_key = next(
                (
                    classification_name
                    for classification_name, classification_value in possible_exam_results.items()
                    if classification_value == result
                ),
                None,
            )
            if not classification_key:
                continue
            classification = possible_classifications[classification_key]
            classifications.append(classification)

        return classifications

    @property
    def f_closing_date(self) -> str:
        return self.investigation_form_data["form:dengue_dataEncerramentoInputDate"]

    @property
    def closing_date(self):
        return datetime.strptime(self.f_closing_date, "%d/%m/%Y")

    @property
    def f_notification_date(self):
        return self.notification_form_data["form:dtNotificacaoInputDate"]

    @property
    def notification_date(self):
        return datetime.strptime(self.f_notification_date, "%d/%m/%Y")

    @property
    def notification_number(self) -> str:
        return self.notification_form_data["form:nuNotificacao"]

    @property
    def position(self):
        return self.positions_history[-1]

    @position.setter
    def position(self, value: POSSIBLE_POSITIONS):
        getattr(self, "_positions_history", []).append(value)

    @property
    def positions_history(self) -> list[POSSIBLE_POSITIONS]:
        return getattr(self, "_positions_history", ["results"])

    @property
    def priority(self) -> int:
        priority_queue = []
        if self.dengue_classification in ("11", "12"):
            priority_queue.append(
                PRIORITY_CLASSIFICATION_MAP[self.dengue_classification]
            )

        # if have at least one classification as "10"
        if any(map(lambda k: k == "10", self.classifications)):
            priority_queue.append(PRIORITY_CLASSIFICATION_MAP["10"])

        # if have at least one classification as "5", so added the priority of 5
        if any(map(lambda k: k == "5", self.classifications)):
            priority_queue.append(PRIORITY_CLASSIFICATION_MAP["5"])

        return max(priority_queue)

    @property
    def mother_name(self) -> str:
        """The mother name on the notification sheet"""
        return self.notification_form_data["form:notificacao_nome_mae"]


class Sheet(Properties):
    """The sheet class used to interact with the sheets in the investigation
    - Notification methods
    - Investigation methods
    """

    def __init__(
        self,
        session: Session,
        patient: Patient,
        search_result_data: dict,
        open_payload: dict,
        reporter: Report,
    ):
        self.session = session
        self.patient = patient
        self.search_result_data = search_result_data
        self.open_payload = open_payload
        self.reporter = reporter
        self.open_notification_endpoint = (
            f"{SINAN_BASE_URL}/sinan/secured/consultar/consultarNotificacao.jsf"
        )
        self.master_endpoint = f"{SINAN_BASE_URL}/sinan/secured/notificacao/individual/dengue/dengueIndividual.jsf"

        self.has_previous_investigation = None
        self._positions_history: list[POSSIBLE_POSITIONS] = ["results"]

        self.__open_notification_sheet()
        self.return_to_results_page()

    def __open_notification_sheet(self):
        """Open the notification sheed using the `open_payload`"""
        if self.position != "results":
            print(
                "[ERRO] Para abrir a notificação, é necessário estar na aba de resultados."
            )
            return

        res = self.session.post(self.open_notification_endpoint, self.open_payload)
        self.notification_soup = BeautifulSoup(res.content, "html.parser")
        self.position = "notification"

        self.__loads_notification_form_data()

    def __loads_notification_form_data(self):
        """Given the `notification_soup` loads the notification form data as a dict"""
        if "notification" not in self.positions_history:
            print(
                "[ERRO] Para carregar o formulário de notificação se faz necessário ter passado pela aba de notificação ao menos uma vez."
            )
            return

        self.notification_form_data = get_form_data(self.notification_soup)
        self.notification_form_data.update(
            {"javax.faces.ViewState": self.javax_view_state}
        )

    def __loads_investigation_form_data(self):
        """Given the `investigation_soup` loads the investigation form data as a dict"""
        if "investigation" not in self.positions_history:
            print(
                "[ERRO] Para carregar o formulário de investigação se faz necessário ter passado pela aba de investigação ao menos uma vez."
            )
            return
        self.investigation_form_data = get_form_data(self.investigation_soup)
        self.investigation_form_data.update(
            {"javax.faces.ViewState": self.javax_view_state}
        )

    def __click_popup_ok(self, depth: int):
        """ "Click" in "Ok" buttom if modal appears in the response"""
        soup = self.investigation_soup

        show_modal_script = next(
            (
                s
                for s in soup.find_all("script")
                if s.text.strip().endswith(".component.show();")
            ),
            None,
        )

        if not show_modal_script:
            self.reporter.error(
                "Código que mostra o popUp não foi encontrado na resposta do servidor. Provável mudança no site.",
                "Paciente não pôde ser investigado.",
            )
            raise FileNotFoundError("Script pra mostrar o popUp não encontrado.")

        show_modal_text = "".join(show_modal_script.text.split("\n")).strip()

        modal_id_match = re.search(
            r"getElementById\(['\"]([^'\"]+)['\"]\)", show_modal_text
        )
        if not modal_id_match:
            self.reporter.error(
                "ID do popUp não encontrado na resposta do servidor.",
                "Paciente não pôde ser investigado.",
            )
            raise FileNotFoundError(
                "ID do popUp não encontrado na resposta do servidor."
            )

        modal_id = modal_id_match.group(1)
        modal_text = soup.find("div", {"id": modal_id}).get_text(strip=True)  # type: ignore [fé]

        self.reporter.info(f"Texto do popUp {depth}: {modal_text}")

        payload_modal_ok = get_form_data(soup, "div", {"id": modal_id})
        payload_modal_ok = {
            k: v for k, v in payload_modal_ok.items() if "ok" in v.lower()
        }

        payload = get_form_data(soup)
        payload.update(payload_modal_ok)

        print("[INVESTIGAÇÃO] Clicando em 'Ok' para continuar.", end=" ")
        res = self.session.post(
            self.master_endpoint,
            data=payload,
        )

        self.investigation_soup = BeautifulSoup(res.content, "html.parser")
        print("Ok!")

        self.__verify_investigation_sheet(depth + 1)

    def __verify_investigation_sheet(self, depth: int = 1, retry: bool = True) -> bool:
        """Verify if the `investigation_soup` is really the investigation page or a different page"""
        first_investigation_input = valid_tag(
            self.investigation_soup.find(attrs={"id": "form:dtInvestigacaoInputDate"})
        )

        if not first_investigation_input:
            if retry:
                self.__click_popup_ok(depth)
        else:
            self.position = "investigation"

        return first_investigation_input is not None

    def __update_notification_form_data_javascript_rendering(self):
        """Update the `notification_form_data` to be equal to the form data rendered in javascript on page load"""
        self.notification_form_data.update(
            {
                "form:richagravo": self.notification_form_data[
                    "form:richagravocomboboxField"
                ],
                "form:notificacao_unidadeSaude_municipio_noMunicipio": self.notification_form_data[
                    "form:notificacao_unidadeSaude_municipio_noMunicipiocomboboxField"
                ],
                "form:notificacao_unidadeSaude_estabelecimento": self.notification_form_data[
                    "form:notificacao_unidadeSaude_estabelecimentocomboboxField"
                ],
                "form:notificacao_paciente_endereco_municipio_noMunicipio": self.notification_form_data[
                    "form:notificacao_paciente_endereco_municipio_noMunicipiocomboboxField"
                ],
                "form:notificacao_paciente_endereco_bairro_noBairro": self.notification_form_data[
                    "form:notificacao_paciente_endereco_bairro_noBairrocomboboxField"
                ],
                "form:notificacao_paciente_endereco_municipio_uf_pais_noPais": self.notification_form_data[
                    "form:notificacao_paciente_endereco_municipio_uf_pais_noPaiscomboboxField"
                ],
            }
        )

    def __enable_investigation_sheet(self):
        """Try to enable the investigation tab "clicking" in "Salvar" and "Ok" buttons"""

        self.__update_notification_form_data_javascript_rendering()

        res = self.session.post(
            self.master_endpoint,
            {**self.notification_form_data, "form:botaoSalvar": "Salvar"},
        )

        self.investigation_soup = BeautifulSoup(res.content, "html.parser")

        self.__verify_investigation_sheet()

    def __navigate_investigation_sheet(self):
        """Navigate to the investigation tab"""

        self.__update_notification_form_data_javascript_rendering()

        res = self.session.post(
            self.master_endpoint,
            {
                **self.notification_form_data,
                "form:tabInvestigacao": "form:tabInvestigacao",
            },
        )

        self.investigation_soup = BeautifulSoup(res.content, "html.parser")

        result = self.__verify_investigation_sheet(retry=False)
        if not result:
            error_filename = f"error_{self.patient.name}.html"
            with open(error_filename, "wb") as f:
                f.write(res.content)
            print(
                "[ERRO] Falha ao carregar a aba de investigação. Erro precisa ser tratado pelo programador."
            )
            self.reporter.error(
                "Falha ao carregar a aba de investigação.",
                f"Um arquivo com a resposta do servidor foi criado com o nome de {error_filename}.",
            )

    def __open_investigation_sheet(self):
        """Open investigation sheet enabling the investigation tab if it is disabled"""
        if self.position != "results":
            print(
                "[ERRO] Para abrir a aba de investigação, é preciso estar na aba de resultados (resultado -> notificação -> investigação)."
            )
            return

        self.__open_notification_sheet()

        self.has_previous_investigation = self.is_investigation_sheet_enabled

        if not self.is_investigation_sheet_enabled:
            self.reporter.warn(
                "Aba de investigação não está habilitada. Habilitando..."
            )
            self.__enable_investigation_sheet()
        else:
            self.reporter.info("Aba de investigação já está habilitada.")
            self.__navigate_investigation_sheet()

        self.__loads_investigation_form_data()

    @property
    def is_oportunity(self) -> bool:
        """Check if the patient is oportunity to be investigated"""
        if "notification" not in self.positions_history:
            print(
                "[ERRO] Para verificar se o paciente é oportuno, é preciso ter passado pela aba de notificação ao menos uma vez."
            )
            return False

        self.reporter.set_patient(self.patient)

        rules = {
            "IgM": lambda time: time + timedelta(days=1) >= timedelta(days=6),
            "NS1": lambda time: time <= timedelta(days=5),
            "PCR": lambda time: time <= timedelta(days=5),
        }

        if not self.patient.exam_type or self.patient.exam_type not in rules:
            self.reporter.error(
                f"Ao tentar verificar oportunidade do paciente, o bot encontrou um tipo de exame inválido: {self.patient.exam_type}.",
                "Oportunidade definida como Falsa.",
            )
            return False

        rule = rules[self.patient.exam_type]
        elapsed_time = self.patient.collection_date - self.first_symptoms_date

        if elapsed_time.days < 0:
            self.reporter.warn(
                "Ficha de notificação desconsiderada (inoportuna) uma vez que a diferença entre Data de Coleta e a Data de 1ºs Sintomas é negativa.",
                f"Número da Notificação: {self.notification_number} | Data de Notificação ({self.f_first_symptoms_date}) - Data de Coleta ({self.patient.f_collection_date}) = {elapsed_time.days} dias.",
            )
            return False

        result = rule(elapsed_time)

        if result:
            self.reporter.info(
                "Ficha de notificação considerada oportuna.",
                f"Número da Notificação: {self.notification_number} | Data de Notificação ({self.f_first_symptoms_date}) - Data de Coleta ({self.patient.f_collection_date}) = {elapsed_time.days} dias.",
            )
        else:
            self.reporter.info(
                "Ficha de notificação NÃO considerada oportuna.",
                f"Número da Notificação: {self.notification_number} | Data de Notificação ({self.f_first_symptoms_date}) - Data de Coleta ({self.patient.f_collection_date}) = {elapsed_time.days} dias.",
            )

        return result

    @property
    def is_closed_by_municipality(self) -> bool:
        """Check if the notification was closed by municipality"""
        if "notification" not in self.positions_history:
            print(
                "[ERRO] Para verificar se a ficha foi encerrado pelo município, é preciso ter passado pela aba de notificação ao menos uma vez."
            )
            return False

        input_tag = valid_tag(
            self.notification_soup.find("input", {"id": "form:habilitaAntesPrazo"})
        )

        if not input_tag:
            self.reporter.error(
                "Ao tentar verificar se a ficha foi encerrada pelo município o bot encontrou um elemento inválido.",
                "Status de encerrado pelo município definido como Falso.",
            )
            return False

        return (
            input_tag.get("checked") == "checked"
            and input_tag.get("disabled") == "disabled"
        )

    def __save_investigation(self):
        """Save the investigation filled form"""
        payload = get_form_data(self.investigation_soup)
        payload.update({"form:btnSalvarInvestigacao": "form:btnSalvarInvestigacao"})

        res = self.session.post(self.master_endpoint, data=payload)
        soup = BeautifulSoup(res.content, "html.parser")
        errors_txt = False
        if errors := soup.find_all("li", {"class": "error"}):
            errors_txt = "\n".join(
                [error.get_text() for error in errors if error.get_text()]
            )

        if errors_txt:
            self.reporter.error(
                "Ao tentar salvar a investigação o site retornou esta mensagem de erro (ver observações)",
                errors_txt,
            )
            print("Erro!")
            print(f"\tMensagem do Site: '{errors_txt}'")
        else:
            print("Ok!")

    def __fill_exam_result(self):
        """Fill the exam result on sinan investigation form

        Possible Inputs that can be filled:
            39, 41, 45 - Data da Coleta,
            40, 42, 46 - Resultado,
            47 - Sorotipo
        """

        # TODO: define setters for collection date keys and collection result keys for each exam type

        if self.patient.exam_type == "PCR":
            sinan_collection_date_key = "form:dengue_dataColetaRTPCRInputDate"
            sinan_collection_result_key = "form:dengue_resultadoRTPCR"
            self.investigation_form_data.update(
                {
                    sinan_collection_date_key: self.patient.f_collection_date,
                    sinan_collection_result_key: self.patient.sinan_result_id,
                }
            )

            self.session.post(
                self.master_endpoint,
                data={**self.investigation_form_data, "form:j_id572": "form:j_id572"},
            )

            if self.patient.sinan_result_id == "1":
                sotorype_dengue = max(
                    self.patient.sorotypes, key=lambda s: int(s.removeprefix("DENV"))
                )

                if len(self.patient.sorotypes) > 1:
                    self.reporter.warn(
                        f"Dos {len(self.patient.sorotypes)} sorotipos ({self.patient.sorotypes}), foi selecionado o sorotipo {sotorype_dengue}.",
                    )

                self.investigation_form_data.update(
                    {
                        "form:dengue_sorotipo": sotorype_dengue.removeprefix("DENV"),
                    }
                )

                self.session.post(
                    self.master_endpoint,
                    data={
                        **self.investigation_form_data,
                        "form:j_id577": "form:j_id577",
                    },
                )

        elif self.patient.exam_type == "IgM":
            sinan_collection_date_key = "form:dengue_dataColetaExameSorologicoInputDate"
            sinan_collection_result_key = "form:dengue_resultadoExameSorologico"

            self.investigation_form_data.update(
                {
                    sinan_collection_date_key: self.patient.f_collection_date,
                    sinan_collection_result_key: self.patient.sinan_result_id,
                }
            )

        elif self.patient.exam_type == "NS1":
            sinan_collection_date_key = "form:dengue_dataColetaNS1InputDate"
            sinan_collection_result_key = "form:dengue_resultadoNS1"

            self.investigation_form_data.update(
                {
                    sinan_collection_date_key: self.patient.f_collection_date,
                    sinan_collection_result_key: self.patient.sinan_result_id,
                }
            )

        print(
            f"[PREENCHIMENTO] Definindo resultado para exame tipo {self.patient.exam_type} com data de coleta {self.patient.f_collection_date}."
        )

    def __fill_investigation_date(self):
        """Fill the investigation date field (31 - Data da investigação)"""
        f_today = TODAY_FORMATTED

        if self.f_closing_date:
            if self.closing_date < TODAY:
                self.reporter.warn(
                    f"Data de encerramento no site ({self.f_closing_date}) é menor que a data de hoje ({f_today}). Portanto a data de investigação será definida para a data que está no site: {self.f_closing_date}."
                )
        else:
            self.investigation_form_data.update(
                {"form:dtInvestigacaoInputDate": f_today}
            )
            self.session.post(
                self.master_endpoint,
                data={**self.investigation_form_data, "form:j_id402": "form:j_id402"},
            )

    def __fill_classification(self):
        """Select the classification based on the exam results (62 - Classificação)

        If the classification is already defined to 11 or 12 it will not be changed
        """
        if self.dengue_classification in ("11", "12"):
            self.reporter.warn(
                f"Investigação JÁ possui classificação selecionada: {self.f_dengue_classification}",
                "Permanece classificação definida do site.",
            )
            return

        if any(map(lambda k: k == "10", self.classifications)):
            self.investigation_form_data.update({"form:dengue_classificacao": "10"})
        elif any(map(lambda k: k == "5", self.classifications)):
            self.investigation_form_data.update({"form:dengue_classificacao": "5"})

        classification = self.investigation_form_data["form:dengue_classificacao"]
        if not classification:
            self.reporter.warn(
                "Nenhuma classificação definida para este paciente.",
                "Isto impede a definição da data de encerramento.",
            )
            return

        self.session.post(
            self.master_endpoint,
            data={**self.investigation_form_data, "form:j_id713": "form:j_id713"},
        )
        self.reporter.debug(
            f"Classificação selecionada: {self.f_dengue_classification}"
        )

    def __fill_criteria(self):
        """Select the confirmation criteria (63 - Critério de Confirmação)"""
        self.investigation_form_data.update({"form:dengue_criterio": "1"})
        self.session.post(
            self.master_endpoint,
            data={**self.investigation_form_data, "form:j_id718": "form:j_id718"},
        )

    def __fill_closing_date(self):
        if not self.dengue_classification:
            print(
                "[PREENCHIMENTO] Como nenhuma classificação foi definda a data de encerramento será ignorada."
            )
            return

        considered_date = self.f_closing_date.strip()

        if considered_date:
            if self.closing_date < self.patient.collection_date:
                considered_date = TODAY_FORMATTED
                self.reporter.warn(
                    f"Data de encerramento do sinan ({self.f_closing_date}) é menor que a data de coleta ({self.patient.f_collection_date}). Portanto a data de encerramento será definida para a data que está no site: {self.f_closing_date}."
                )
        elif self.dengue_classification in ("11", "12"):
            print(
                f"Como a classificação já foi selecionada como {self.f_dengue_classification}. A data de encerramento não será definida."
            )
            self.reporter.warn(
                f"Como a classificação já foi selecionada como {self.f_dengue_classification}. A data de encerramento não será definida."
            )
            return
        else:
            considered_date = TODAY_FORMATTED

        self.investigation_form_data.update(
            {"form:dtEncerramentoInputDate": considered_date}
        )

        self.session.post(
            self.master_endpoint,
            {**self.investigation_form_data, "form:j_id739": "form:j_id739"},
        )

    def __fill_clinical_signs(self):
        """Select the clinical signs (33 - Sinais Clinicos)"""
        self.investigation_form_data.update(
            {
                k: ((v or "2") if not self.has_previous_investigation else "2")
                for k, v in self.investigation_form_data.items()
                if k.startswith("form:chikungunya_sinais")
            }
        )

    def __fill_illnesses(self):
        """Select the illnesses (34 - Doencas Pré-existentes)"""
        self.investigation_form_data.update(
            {
                k: ((v or "2") if not self.has_previous_investigation else "2")
                for k, v in self.investigation_form_data.items()
                if k.startswith("form:chikungunya_doencas")
            }
        )

    def investigate_patient(self):
        """Open the investigation sheet page and fill the investigation form with the classification and the patient data"""
        self.__open_investigation_sheet()

        form_builders = [
            self.__fill_exam_result,
            self.__fill_investigation_date,
            self.__fill_classification,
            self.__fill_criteria,
            self.__fill_closing_date,
            self.__fill_clinical_signs,
            self.__fill_illnesses,
        ]

        for form_builder in form_builders:
            form_builder()

        self.__save_investigation()

    def delete(self):
        """Delete the notification sheet"""

        self.__open_notification_sheet()

        self.session.post(
            self.master_endpoint,
            {
                **self.notification_form_data,
                "form:j_id306": "Excluir",
            },
        )
        self.reporter.set_patient(self.patient)

        self.reporter.debug(
            "Notificação excluída.", f"Notificação excluída: {self.notification_number}"
        )

    def return_to_results_page(self):
        """Reset the javax.viewState returning to the results page allowing to open anothers sheets"""
        if self.position != "notification":
            print(
                "[ERRO] Para voltar à página de resultados, é necessário estar na aba de notificação."
            )
            return
        self.session.post(
            self.master_endpoint,
            {**self.notification_form_data, "form:j_id313": "Voltar"},
        )
        self.position = "results"
