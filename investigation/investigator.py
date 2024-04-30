import re
import time
from datetime import datetime
from typing import List, Mapping, Optional

import requests
from bs4 import BeautifulSoup

from core.constants import (
    CLASSIFICATION_FRIENDLY_MAP,
    CLASSSIFICATION_MAP,
    EXAM_RESULT_ID,
    EXAM_VALUE_COL_MAP,
    EXAMS_GAL_MAP,
    POSSIBLE_EXAM_TYPES,
    PRIORITY_CLASSIFICATION_MAP,
    SINAN_BASE_URL,
    TODAY,
    TODAY_FORMATTED,
    NotificationType,
)
from core.utils import valid_tag
from investigation.report import Report


class NotFoundError(Exception):
    """Raised when something in the page was not found."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class Investigator:
    """Given a patient data and your payload to open the Sinan page, this class will be used to investigate the patient."""

    def __init__(self, session: requests.Session, reporter: Report) -> None:
        self.session = session
        self.open_notification_endpoint = (
            f"{SINAN_BASE_URL}/sinan/secured/consultar/consultarNotificacao.jsf"
        )
        self.notification_endpoint = f"{SINAN_BASE_URL}/sinan/secured/notificacao/individual/dengue/dengueIndividual.jsf"
        self.reporter = reporter

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
            raise NotFoundError(f"Formulário <{tag_name} {attrs} /> não encontrado.")

        def get_value(input_tag):
            input_type = input_tag.get("type", "text")
            if input_type == "checkbox":
                checked = input_tag.get("checked", "")
                return "on" if checked else ""
            return input_tag.get("value", "")

        # for each input, get the name and value
        inputs = {i.get("name", ""): get_value(i) for i in form.find_all("input")}

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

    def __submit_modal_ok(self, clicks: int):
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
            self.reporter.error(
                "Script que mostra o popUp não foi encontrado na resposta do servidor. Provável mudança no site."
                "Paciente não pôde ser investigado."
            )
            raise NotFoundError("Script pra mostrar o popUp não encontrado.")

        show_modal_text = "".join(show_modal_script.text.split("\n")).strip()

        modal_id_match = re.search(
            r"getElementById\(['\"]([^'\"]+)['\"]\)", show_modal_text
        )
        if not modal_id_match:
            self.reporter.error(
                "ID do popUp não encontrado na resposta do servidor.",
                "Paciente não pôde ser investigado.",
            )
            raise NotFoundError("ID do popUp não encontrado na resposta do servidor.")

        modal_id = modal_id_match.group(1)
        modal_text = self.soup.find("div", {"id": modal_id}).get_text(strip=True)  # type: ignore [fé]
        self.reporter.info(f"Texto do popUp {clicks}: {modal_text}")
        payload_modal_ok = self.__get_form_data("div", {"id": modal_id})
        payload_modal_ok = {
            k: v for k, v in payload_modal_ok.items() if "ok" in v.lower()
        }
        self.current_form.pop("form:botaoSalvar", None)

        print("[INVESTIGAÇÃO] Clicando em 'Ok' para continuar.", end=" ")
        response = self.session.post(
            self.notification_endpoint,
            data={**self.current_form, **payload_modal_ok},
        )
        self.soup = BeautifulSoup(response.content, "html.parser")

        print("Ok!")
        return self.__finish_open_investigation(clicks + 1)

    def __finish_open_investigation(self, clicks: int = 1):
        first_investigation_input = valid_tag(
            self.soup.find("input", attrs={"id": "form:dtInvestigacaoInputDate"})
        )
        # when there is no investigation form, so probabilly exists a modal being shown
        if not first_investigation_input:
            try:
                print(
                    f"[INVESTIGAÇÃO] Apareceu um popUp ao tentar salvar a Notificação. Clicando em 'Ok' para continuar ({clicks})."
                )
                self.__submit_modal_ok(clicks)
            except ValueError:
                # TODO: handle modal not found
                pass

    def __enable_and_open_investigation(self):
        """Enable the investigation aba and open it (the response form)

        Args:
            form_data (dict): The patient form data to open investigation
        """
        print("[INVESTIGAÇÃO] Abrindo aba de investigação.")
        self.current_form = self.__get_form_data()
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
                "form:richagravo": self.current_form["form:richagravocomboboxField"],
                "form:notificacao_unidadeSaude_municipio_noMunicipio": self.current_form[
                    "form:notificacao_unidadeSaude_municipio_noMunicipiocomboboxField"
                ],
                "form:notificacao_unidadeSaude_estabelecimento": self.current_form[
                    "form:notificacao_unidadeSaude_estabelecimentocomboboxField"
                ],
                "form:notificacao_paciente_endereco_municipio_noMunicipio": self.current_form[
                    "form:notificacao_paciente_endereco_municipio_noMunicipiocomboboxField"
                ],
                "form:notificacao_paciente_endereco_bairro_noBairro": self.current_form[
                    "form:notificacao_paciente_endereco_bairro_noBairrocomboboxField"
                ],
                "form:notificacao_paciente_endereco_municipio_uf_pais_noPais": self.current_form[
                    "form:notificacao_paciente_endereco_municipio_uf_pais_noPaiscomboboxField"
                ],
            }
        )
        response = self.session.post(self.notification_endpoint, data=self.current_form)
        self.soup = BeautifulSoup(response.content, "html.parser")

        self.__finish_open_investigation()

    def __define_exam_result_data(self):
        """Get the payload with the exam result which is one of the options in the Sinan Investigation Form and fill the exam result.

        Possible Inputs that can be filled:
            39, 41, 45 - Data da Coleta,
            40, 42, 46 - Resultado,
            47 - Sorotipo
        """
        exam_type = EXAMS_GAL_MAP[self.patient_data["Exame"]]
        print(f"[PREENCHIMENTO] Definindo resultado para exame tipo {exam_type}.")
        exam_result_map = EXAM_RESULT_ID[exam_type]
        formatted_collection_date = self.patient_data["Data da Coleta"].strftime(
            "%d/%m/%Y"
        )

        if exam_type == "PCR":
            patient_data_result_column = EXAM_VALUE_COL_MAP[exam_type]
            payload_collection_date_column = "form:dengue_dataColetaRTPCRInputDate"
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
                sorotypes = self.patient_data["Sorotipo"].split(" e ")
                sorotype_dengue = max(
                    sorotypes, key=lambda sorotype: int(sorotype.removeprefix("DENV"))
                )  # DENV1, DENV2, etc.
                if len(sorotypes) > 1:
                    self.reporter.warn(
                        f"Dos {len(sorotypes)} sorotipos ({'; '.join(sorotypes)}), foi escolhido o maior: {sorotype_dengue}."
                    )
                self.current_form.update(
                    {
                        "form:dengue_sorotipo": sorotype_dengue.removeprefix("DENV"),
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
            payload_collection_result_column = "form:dengue_resultadoExameSorologico"
            exam_result = str(self.patient_data[patient_data_result_column])
            payload_exam_result = exam_result_map.get(exam_result)

            if not payload_exam_result:
                raise Exception("Não foi possível definir o resultado do exame.")

            self.current_form.update(
                {
                    payload_collection_date_column: formatted_collection_date,
                    payload_collection_result_column: payload_exam_result,
                }
            )

        elif exam_type == "NS1":
            patient_data_result_column = EXAM_VALUE_COL_MAP[exam_type]
            payload_collection_date_column = "form:dengue_dataColetaNS1InputDate"
            payload_collection_result_column = "form:dengue_resultadoNS1"
            exam_result = self.patient_data[patient_data_result_column]
            payload_exam_result = exam_result_map[exam_result]
            self.current_form.update(
                {
                    payload_collection_date_column: formatted_collection_date,
                    payload_collection_result_column: payload_exam_result,
                }
            )
        else:
            raise Exception("O tipo de exame não foi definido corretamente.")

        print(
            f"[PREENCHIMENTO] Resultado do exame: {exam_result} | Data da Coleta: {formatted_collection_date}"
        )

    def __get_classifications(
        self, exam_results: Mapping[POSSIBLE_EXAM_TYPES, str | None]
    ):
        classifications = []
        for exam_type, result in exam_results.items():
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

    def __select_classification(self):
        """Select the classification based on the exam results (62 - Classificação)"""
        if self.current_form["form:dengue_classificacao"] in ("11", "12"):
            classification = self.current_form["form:dengue_classificacao"]
            self.reporter.warn(
                f"Investigação JÁ possui classificação: {CLASSIFICATION_FRIENDLY_MAP[classification]}",
                "Permanece classificação definida do site.",
            )
            print(
                f"[PREENCHIMENTO] Classificação JÁ selecionada como '{CLASSIFICATION_FRIENDLY_MAP[classification]}'."
            )
            return

        exam_results: Mapping[POSSIBLE_EXAM_TYPES, str | None] = {
            "IgM": self.current_form["form:dengue_resultadoExameSorologico"],
            "NS1": self.current_form["form:dengue_resultadoNS1"],
            "PCR": self.current_form["form:dengue_resultadoRTPCR"],
        }

        classifications = self.__get_classifications(exam_results)

        if any(map(lambda k: k == "10", classifications)):
            self.current_form.update({"form:dengue_classificacao": "10"})
        elif any(map(lambda k: k == "5", classifications)):
            self.current_form.update({"form:dengue_classificacao": "5"})

        classification = self.current_form["form:dengue_classificacao"]
        if not classification:
            print("[PREENCHIMENTO] Nenhuma classificação definida para este paciente.")
            self.reporter.warn(
                "Nenhuma classificação definida para este paciente.",
                "Isto impede a definição da data de encerramento.",
            )
            return

        self.session.post(
            self.notification_endpoint,
            data={**self.current_form, "form:j_id713": "form:j_id713"},
        )
        self.reporter.debug(
            f"Classificação selecionada: {CLASSIFICATION_FRIENDLY_MAP[self.current_form['form:dengue_classificacao']]}"
        )
        print(
            f"[PREENCHIMENTO] Classificação selecionada: {CLASSIFICATION_FRIENDLY_MAP[self.current_form['form:dengue_classificacao']]}"
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
        print("[PREENCHIMENTO] Definindo Data de Encerramento.", end=" ")
        if not self.current_form["form:dengue_classificacao"]:
            print("Classificação não definida. Ignorando data de encerramento.")
            return
        date_considered = self.current_form[
            "form:dengue_dataEncerramentoInputDate"
        ].strip()
        if date_considered:
            date_site = datetime.strptime(date_considered, "%d/%m/%Y")
            if date_site < self.patient_data["Data da Coleta"]:
                date_considered = TODAY_FORMATTED
                self.reporter.warn(
                    f"Data de encerramento do site ({date_site}) é menor que a data da coleta ({self.patient_data['Data da Coleta'].strftime('%d/%m/%Y')}). Portanto será utilizada a data de hoje ({date_considered}) para o encerramento."
                )
        elif self.current_form["form:dengue_classificacao"] in ("11", "12"):
            print(
                f"Classificação selecionada como '{CLASSIFICATION_FRIENDLY_MAP[self.current_form['form:dengue_classificacao']]}'. Ignorado."
            )
            self.reporter.warn(
                f"Não foi definido data de encerramento pois classificação está selecionada como {CLASSIFICATION_FRIENDLY_MAP[self.current_form['form:dengue_classificacao']]}"
            )
            return
        else:
            date_considered = TODAY_FORMATTED

        self.current_form.update(
            {"form:dengue_dataEncerramentoInputDate": date_considered}
        )
        self.session.post(
            self.notification_endpoint,
            data={**self.current_form, "form:j_id739": "form:j_id739"},
        )
        print(f"Data de encerramento utilizada: {date_considered}. Ok!")

    def __define_investigation_date(self):
        """Define the investigation date (31 - Data da Investigação)"""
        print("[PRRENCHIMENTO] Tentando definir 31 - Data da Investigação.", end=" ")
        today_formatted = TODAY_FORMATTED
        closing_date_formatted = self.current_form[
            "form:dengue_dataEncerramentoInputDate"
        ]

        if closing_date_formatted:
            closing_date = datetime.strptime(closing_date_formatted, "%d/%m/%Y")
            if closing_date < TODAY:
                self.reporter.warn(
                    f"Data de encerramento no site ({closing_date_formatted}) é menor que a data de hoje ({today_formatted}). Portanto a data de investigação será definida para a data que está no site: {self.current_form['form:dtInvestigacaoInputDate']}."
                )
        else:
            self.current_form.update({"form:dtInvestigacaoInputDate": today_formatted})
            self.session.post(
                self.notification_endpoint,
                data={**self.current_form, "form:j_id402": "form:j_id402"},
            )
        print(f"Data de investigação definida: {today_formatted}. Ok!")

    def __select_clinical_signs(self):
        """Select the clinical signs (33 - Sinais Clinicos)"""
        self.current_form.update(
            {
                k: ((v or "2") if not self.force_clinal_signs_and_illnesses else "2")
                for k, v in self.current_form.items()
                if k.startswith("form:chikungunya_sinais")
            }
        )

    def __select_illnesses(self):
        """Select the illnesses (34 - Doencas Pré-existentes)"""
        self.current_form.update(
            {
                k: ((v or "2") if not self.force_clinal_signs_and_illnesses else "2")
                for k, v in self.current_form.items()
                if k.startswith("form:chikungunya_doencas")
            }
        )

    def __save_investigation(self):
        """Save the Investigation filled form date and submit it."""
        print("[INVESTIGAÇÃO] Salvando investigação preenchida.", end=" ")
        self.current_form.update(
            {"form:btnSalvarInvestigacao": "form:btnSalvarInvestigacao"}
        )
        res = self.session.post(self.notification_endpoint, data=self.current_form)
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
        print("Ok!")

    def __fill_patient_data(self):
        """Fill the patient data on the investigation form."""
        print("[INVESTIGAÇÃO] Preenchendo dados do paciente.")
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
        else:
            print("[INVESTIGAÇÃO] Preenchimento Concluído. Salvando.")

        self.__save_investigation()

    def __get_javafaces_view_state(self):
        """Get the javax.faces.ViewState tag from the current page"""
        self._javax_view_state = valid_tag(
            self.soup.find(attrs={"name": "javax.faces.ViewState"})
        )

        if not self._javax_view_state:
            raise FileNotFoundError("Não foi possível obter o token de visualização.")

        self._javax_view_state = self._javax_view_state.get("value")

    def __open_notification_page(self, open_payload: dict, clicks: int = 1):
        """Open the patient's notification page (just the notification page, without doing the investigation)

        Args:
            open_payload (dict): The payload to open the notification
        """
        print(
            f"[INVESTIGAÇÃO] Abrindo ficha de Notificação do paciente ({clicks}).",
            end=" ",
        )
        response = self.session.post(
            self.open_notification_endpoint,
            data=open_payload,
        )
        self.soup = BeautifulSoup(response.content, "html.parser")
        print("Ok!")

    def __is_investigation_tab_enabled(self):
        """Check if the navigation tab is enabled (this must be called when the NOTIFICATION page is open)

        Returns:
            bool: True if the navigation tab is enabled
        """
        investigation_tab = valid_tag(
            self.soup.find(attrs={"id": "form:tabInvestigacao_lbl"})
        )
        if not investigation_tab:
            print("[INVESTIGAÇÃO] Erro: A aba de investigação não foi encontrada.")
            raise FileNotFoundError

        return "rich-tab-disabled" in (investigation_tab.get("class") or [])

    def __open_investigation_page(self, open_payload: dict, clicks: int = 1):
        """Open the investigation page that will be used to fill the patient exam data

        Args:
            open_payload (dict): The payload to open the investigation (from the Sinan Researcher class)
        """
        self.__open_notification_page(open_payload, clicks)

        self.__get_javafaces_view_state()
        self.force_clinal_signs_and_illnesses = self.__is_investigation_tab_enabled()
        self.__enable_and_open_investigation()

    def investigate(
        self,
        patient_data: dict,
        open_payload: dict,
    ):
        """Investigate an patient filling out the patient data on the Sinan Investigation page

        Args:
            patient_data (dict): The patient date came from the data loader (SINAN + GAL datasets)
            open_payload (dict): The payload to open the investigation (from the Sinan Researcher class)
        """
        start_time = time.time()
        try:
            self.patient_data = patient_data
            self.__open_investigation_page(open_payload)

            self.current_form = self.__get_form_data()

            self.__fill_patient_data()
        except NotFoundError as e:
            print(f"[INVESTIGAÇÃO] Erro: {e}")
            self.reporter.error("Erro na investigação (ver observações)", str(e))
            with open(
                f"investigação - {self.patient_data['Paciente']}.html",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(self.soup.prettify())
            return
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.reporter.debug(
            f"Tempo para esta investigação foi de {elapsed_time:.2f} segundos"
        )

    def __get_notification_date(self) -> Optional[datetime]:
        """Get the notification date from the notification page

        Returns:
            datetime: The parsed notification date
            None: If some error occurs
        """
        notification_date = valid_tag(
            self.soup.find(attrs={"id": "form:dtNotificacaoInputDate"})
        )
        if not notification_date:
            raise NotFoundError("Não foi possível obter a data de notificação.")

        notification_date_str = notification_date.get("value")

        if isinstance(notification_date_str, list):
            notification_date_str = next(iter(notification_date_str), None)

        if not notification_date_str:
            raise NotFoundError(
                "Não foi possível obter a data de notificação. (O campo está vazio (?))"
            )

        try:
            date = datetime.strptime(notification_date_str, "%d/%m/%Y")
        except ValueError:
            raise NotFoundError(
                f"Não foi possível obter a data de notificação. (O formato não é o esperado): {notification_date_str}"
            )
        return date

    def __compare_investigations_data(
        self, investigations: list[dict[str, dict[str, str]]]
    ):
        IGM_INPUT_NAME = "form:dengue_resultadoExameSorologico"
        PCR_INPUT_NAME = "form:dengue_resultadoRTPCR"
        NS1_INPUT_NAME = "form:dengue_resultadoNS1"
        CLASSIFICATION_INPUT_NAME = "form:dengue_classificacao"
        # o código abaixo vai perder um pouco a qualidade pq estou com preguiça, depois eu reescrevo.

        priority_queue = []

        for investigation in investigations:
            form_data = investigation["form_data"]
            notification_date = investigation["notification"]["notification_date"]
            exam_results: Mapping[POSSIBLE_EXAM_TYPES, str | None] = {
                "IgM": form_data[IGM_INPUT_NAME],
                "NS1": form_data[NS1_INPUT_NAME],
                "PCR": form_data[PCR_INPUT_NAME],
            }
            exam_classification = form_data[CLASSIFICATION_INPUT_NAME]

            if exam_classification in ("11", "12"):
                priority_queue.append(
                    (
                        PRIORITY_CLASSIFICATION_MAP[exam_classification],
                        notification_date,
                        investigation,
                    )
                )
                continue

            classifications = self.__get_classifications(exam_results)
            if any(map(lambda k: k == "10", classifications)):
                priority_queue.append(
                    (
                        PRIORITY_CLASSIFICATION_MAP["10"],
                        notification_date,
                        investigation,
                    )
                )

            elif any(map(lambda k: k == "5", classifications)):
                priority_queue.append(
                    (PRIORITY_CLASSIFICATION_MAP["5"], notification_date, investigation)
                )
            else:
                priority_queue.append((100, notification_date, investigation))

        # sort by priority (x[0]) and the oldest notification date per priority (x[1])
        priority_queue.sort(key=lambda x: (x[0], x[1]))

        return priority_queue[:1], priority_queue[1:]

    def __avalie_notifications(
        self, notifications: list[NotificationType]
    ) -> tuple[list[NotificationType], list[NotificationType]]:
        """Compare all notifications (results) and define what will be considered and what will be discarded

        As defined in the Google Doc document:
        1. No result has investigation: Consider only the oldest notification and descard others
        2. Every result has investigation: Compare all notifications as defined in the Google Doc document
        3. Results with investigation and without investigation: Consider only notifications with investigation and descard others

        Args:
            notifications (list[NotificationType]): List of notifications

        Returns:
            tuple[list[NotificationType], list[NotificationType]]: List of considered notifications and list of discarded notifications
                `(considered, discarded)`
        """
        considered: list[NotificationType] = []
        discarded: list[NotificationType] = []

        # 1. No result has investigation: Consider only the oldest notification and descard others
        if not all(notification["has_investigation"] for notification in notifications):
            print(
                "[INVESTIGAÇÃO MÚLTIPLA] Todas as Notificações NÃO possuem ficha de investigação."
            )
            notification_considered = min(
                notifications, key=lambda n: n["notification_date"]
            )
            considered.append(notification_considered)
            discarded.extend(
                [
                    notification
                    for notification in notifications
                    if notification != notification_considered
                ]
            )

        # 2. Every result has investigation: Compare all notifications exams as defined in the Google Doc document
        elif all(notification["has_investigation"] for notification in notifications):
            print(
                "[INVESTIGAÇÃO MÚLTIPLA] Todas as Notificações POSSUEM ficha de investigação."
            )
            notifications_data = []
            for i, notification in enumerate(notifications, 1):
                self.__open_investigation_page(notification["open_payload"], i)
                investigation_form_data = self.__get_form_data()
                notifications_data.append(
                    {"notification": notification, "form_data": investigation_form_data}
                )

            considered, discarded = self.__compare_investigations_data(
                notifications_data
            )

        # 3. Results with investigation and without investigation: Consider only notifications with investigation and descard others
        else:
            print(
                "[INVESTIGAÇÃO MÚLTIPLA] Algumas notificações com ficha de investigação e outras sem ficha de investigação."
            )
            for notification in notifications:
                if notification["has_investigation"]:
                    considered.append(notification)
                else:
                    discarded.append(notification)

        return considered, discarded

    def __discard_notification(self, open_payload: dict):
        """Discard the notification on the Sinan Investigation page

        Args:
            open_payload (dict): The payload to open the notification
        """
        self.__open_notification_page(open_payload)
        form = self.__get_form_data()
        form.pop("form:botaoSalvar", None)
        self.__get_javafaces_view_state()
        form.update(
            {"form:j_id306": "Excluir", "javax.faces.ViewState": self._javax_view_state}
        )
        # TODO: Uncomment this line to actually discard the notification
        # self.session.post(self.notification_endpoint, data=form)

    def __return_to_results_page(self):
        form = self.__get_form_data()
        form = {
            k: v
            for k, v in form.items()
            if not k.startswith(("form:btn", "form:botao", "form:j_id"))
        }
        self.__get_javafaces_view_state()
        form.update({"javax.faces.ViewState": self._javax_view_state})

        form.update({"form:j_id313": "Voltar"})
        self.session.post(self.notification_endpoint, data=form)

    def investigate_multiple(self, patient_data: dict, open_payloads: List[dict]):
        """Investigate multiple patients filling out the patient data on the Sinan Investigation page

        Args:
            patients_data (dict): The patient date came from the data loader (SINAN + GAL datasets)
            open_payloads (dict): The payloads to open the notifications (from the Sinan Researcher class)
        """
        notifications: List[NotificationType] = []
        for i, open_payload in enumerate(open_payloads, 1):
            try:
                self.__open_notification_page(open_payload)
                has_investigation = self.__is_investigation_tab_enabled()
                notification_date = self.__get_notification_date()
            except NotFoundError as e:
                self.reporter.error(
                    f"O resultado de índice {i} teve algum erro. (Ver Observações)",
                    str(e),
                )
                return

            if notification_date is None:
                self.reporter.error(
                    f"O resultado de índice {i} teve algum erro ao tentar obter a data da notificação.",
                )
                return

            notifications.append(
                {
                    "has_investigation": has_investigation,
                    "notification_date": notification_date,
                    "open_payload": open_payload,
                },
            )
            self.__return_to_results_page()

        notifications.sort(key=lambda n: n["notification_date"])

        notifications_spaced = [notifications[0]]
        notifications_discarded_by_space = []

        for i, notification in enumerate(notifications[1:], 1):
            diff_days = (
                notification["notification_date"]
                - notifications_spaced[-1]["notification_date"]
            ).days
            if diff_days < 15:
                self.reporter.warn(
                    f"A notificação de data {notification['notification_date'].strftime('%d/%m/%Y')} é muito recente comparada a notificação de data {notifications_spaced[-1]['notification_date'].strftime('%d/%m/%Y')} tendo a diferença de {diff_days} dias. Portanto será excluída."
                )
                notifications_discarded_by_space.append(notification)
            else:
                notifications_spaced.append(notification)

        notifications_considered = []
        notifications_discarded = []

        notifications_considered, notifications_discarded = self.__avalie_notifications(
            notifications_spaced
        )

        for notification_discarded in (
            notifications_discarded + notifications_discarded_by_space
        ):
            print(
                f"[INVESTIGAÇÃO MÚLTIPLA] Notificação de data {notification_discarded['notification_date'].strftime('%d/%m/%Y')} foi excluída."
            )
            self.__discard_notification(notification_discarded["open_payload"])

        if len(notifications_considered) > 1:
            self.investigate_multiple(
                patient_data, [n["open_payload"] for n in notifications_considered]
            )
        elif len(notifications_considered) == 1:
            self.investigate(
                patient_data, next(iter(notifications_considered))["open_payload"]
            )
        else:
            self.reporter.error(
                "Matrix Error, chama o desenvolvedor",
                f"paciente: {patient_data};\n\nnotificações: {notifications}",
            )
            print(
                "[INVESTIGAÇÃO MÚLTIPLA] Nenhuma notificação encontrada. [Matrix Error]"
            )
