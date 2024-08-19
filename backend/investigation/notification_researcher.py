import time
from typing import Callable, Literal, Mapping, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

from core.constants import (
    POSSIBLE_AGRAVOS,
    POSSIBLE_MUNICIPALITIES,
    SEARCH_POSSIBLE_CRITERIAS,
    SINAN_BASE_URL,
)
from core.utils import Printter, generate_search_base_payload, valid_tag
from investigation.patient import Patient
from investigation.report import Report
from investigation.sheet import Sheet

display = Printter("PESQUISA")


class Criterias:
    """Criterias of notification research methods to improve the research filters"""

    def __init__(
        self,
        session: requests.Session,
        criterias: dict,
        reporter: Report,
        endpoint: str,
        base_payload: dict,
    ):
        self.session = session
        self.reporter = reporter
        self.base_payload = base_payload
        self.endpoint = endpoint
        self.criterias = criterias
        self.current_criterias = []

    def __remove_criteria(self, criteria: SEARCH_POSSIBLE_CRITERIAS):
        """Send the payload to remove the one of the filter criterions

        Args:
            criteria (SEARCH_POSSIBLE_CRITERIAS): The filter criterion to be removed
        """
        payload = self.base_payload.copy()
        criteria_index = self.current_criterias.index(criteria)
        remove_criteria_key = f"form:j_id213:{criteria_index}:j_id215"
        payload[remove_criteria_key] = remove_criteria_key
        self.session.post(self.endpoint, data=payload)
        self.current_criterias.pop(criteria_index)

    def __patient_name_criteria(
        self, patient: Patient, field_type_id: str, operator: str
    ):
        """Send the payload to select the patient name criteria on search"""

        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": field_type_id,
                "form:consulta_operador": operator,
                "form:consulta_dsTextoPesquisa": patient.name,
                "form:btnAdicionarCriterio": "form:btnAdicionarCriterio",
            }
        )

        self.session.post(self.endpoint, data=payload)
        self.current_criterias.append("Nome do paciente")

    def __patient_notification_criteria(
        self, patient: Patient, field_type_id: str, operator: str
    ):
        """Send the payload to select the patient notification number criteria on search"""
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": field_type_id,
                "form:consulta_operador": operator,
                "form:consulta_dsTextoPesquisa": patient.notification_number,
                "form:btnAdicionarCriterio": "form:btnAdicionarCriterio",
            }
        )
        self.session.post(self.endpoint, data=payload)
        self.current_criterias.append("Número da Notificação")

    def __patient_date_of_birth_criteria(
        self, patient: Patient, field_type_id: str, operator: str
    ):
        """Send the payload to select the patient date of birth criteria on search"""
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": field_type_id,
                "form:consulta_operador": operator,
                "form:consulta_dsTextoPesquisa": patient.f_birth_date,
                "form:btnAdicionarCriterio": "form:btnAdicionarCriterio",
            }
        )

        self.session.post(self.endpoint, data=payload)
        self.current_criterias.append("Data de nascimento")

    def __patient_mother_name_criteria(
        self, patient: Patient, field_type_id: str, operator: str
    ):
        """Send the payload to select the patient month name criteria on search"""
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": field_type_id,
                "form:consulta_operador": operator,
                "form:consulta_dsTextoPesquisa": patient.mother_name,
                "form:btnAdicionarCriterio": "form:btnAdicionarCriterio",
            }
        )

        self.session.post(self.endpoint, data=payload)
        self.current_criterias.append("Nome da mãe")

    def __select_criteria_field(self, criteria: SEARCH_POSSIBLE_CRITERIAS):
        """Send the payload to select the filter criterion field and load the params on the session

        Args:
            criteria (SEARCH_POSSIBLE_CRITERIAS): The filter criterion

        Returns:
            str: The field type value
        """

        options = self.soup.find("select", {"id": "form:consulta_tipoCampo"}).find_all(  # type: ignore
            "option"
        )
        field_type = next(
            (option for option in options if option.text.strip() == criteria),
            None,
        )

        if not field_type:
            display(
                f"Critério fornecido ({criteria}) não foi encontrado.", category="erro"
            )
            exit(1)

        field_type_value = field_type.get("value")
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": field_type_value,
                "form:j_id161": "Selecione valor no campo",
                "form:j_id136": "form:j_id136",
                "ajaxSingle": "form:consulta_tipoCampo",
            }
        )
        res = self.session.post(self.endpoint, data=payload)
        soup = BeautifulSoup(res.content, "html.parser")
        operator_options = soup.find(
            "select", {"id": "form:consulta_operador"}
        ).find_all("option")  # type: ignore
        operators = {tag.get_text(): tag.get("value") for tag in operator_options}
        return field_type_value, operators

    def add_criteria(
        self,
        criteria: SEARCH_POSSIBLE_CRITERIAS,
        patient: Patient,
    ):
        """Add a filter criterion

        Args:
            criteria (core.constants.SEARCH_POSSIBLE_CRITERIAS): The filter criterion
        """
        criterias = {
            "Nome do paciente": self.__patient_name_criteria,
            "Nome da mãe": self.__patient_mother_name_criteria,
            "Número da Notificação": self.__patient_notification_criteria,
            "Data de nascimento": self.__patient_date_of_birth_criteria,
        }

        field_type_id, operators = self.__select_criteria_field(criteria)

        operation = self.criterias[criteria]["operacao"]
        operator = operators[operation]

        criterias[criteria](patient, field_type_id, operator)


class NotificationResearcher(Criterias):
    """Consult a notification given a patient name

    Args:
        session (requests.Session): Requests session logged obj
        agravo (str): Agravo to filter by (eg. A90 - DENGUE)
        criterios (dict): Criterio configuration (criterios to be used)
        logger (logging.Logger): Logger client.

    Methods:
        consultar(self, patient: str): Consult a notification and return the response
    """

    def __init__(
        self,
        session: requests.Session,
        agravo: POSSIBLE_AGRAVOS,
        municipality: POSSIBLE_MUNICIPALITIES,
        criterias: dict,
        reporter: Report,
    ):
        base_payload = generate_search_base_payload(agravo)
        endpoint = f"{SINAN_BASE_URL}/sinan/secured/consultar/consultarNotificacao.jsf"

        self.municipality: POSSIBLE_MUNICIPALITIES = municipality

        super().__init__(session, criterias, reporter, endpoint, base_payload)

    def __select_agravo(self):
        """Send the payload to select the agravo"""
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:j_id108": "form:j_id108",
                "AJAX:EVENTS_COUNT": "1",
            }
        )
        self.session.post(self.endpoint, data=payload)

    def __search(self):
        """Send the payload to search the notification given the patient name

        Returns:
            requests.Response: The response from the Sinan website
        """
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:btnPesquisar": "form:btnPesquisar",
            }
        )
        res = self.session.post(self.endpoint, data=payload)
        return res

    def __define_javax_faces(self):
        """Loads endpoint page and extract the javax.faces.ViewState this session"""
        res = self.session.get(self.endpoint)
        self.soup = BeautifulSoup(res.content, "html.parser")
        javax_faces = valid_tag(
            self.soup.find("input", {"name": "javax.faces.ViewState"})
        )
        if not javax_faces:
            display("Token de estado de visualização não encontrado.", category="erro")
            exit(1)

        self.base_payload["javax.faces.ViewState"] = javax_faces.get("value")  # type: ignore

    def __check_mother_names(
        self, results: list[Sheet], strategy: Literal["equal", "contains"] = "equal"
    ):
        """Filter the results by mother name using the comparator "equal"

        Args:
            results (list[Sheet]): The list of results to be filtered
            strategy (Literal['equal', 'contains'], optional): The strategy to use. Defaults to "equal".
        """
        strategies: Mapping[Literal["equal", "contains"], Callable[[Sheet], bool]] = {
            "equal": lambda x: x.mother_name == self.patient.mother_name,
            "contains": lambda x: self.patient.mother_name.lower()
            in x.mother_name.lower(),
        }

        _results = []
        for result in results:
            if strategies[strategy](result):
                _results.append(result)
            else:
                self.reporter.warn(
                    "Resultado será ignorado pelo critério de nome de mãe.",
                    f"Nº da Notificação: {result.notification_number} | Estratégia Utilizada: {strategy}",
                )

        return _results

    def search(
        self,
        patient: Patient,
        use_notification_number: bool = False,
        start_time: Optional[float] = None,
    ):
        """Search for a patient in the Sinan website (Consultar Notificação)

        Args:
            patient (Patient): The patient data from GAL to search
            start_time (Optional[float], optional): The start time of the search. Defaults to None.

        Returns:
            list[Sheet]: A list of results with objects to interact with.
        """
        start_time = start_time or time.time()
        self.patient = patient
        self.reporter.set_patient(patient)
        display(f"Pesquisando pelo paciente {patient.name}")
        self.__define_javax_faces()
        self.__select_agravo()

        criterias: list[SEARCH_POSSIBLE_CRITERIAS] = []
        if use_notification_number:
            if pd.isna(patient.notification_number):
                display(
                    "Este paciente não possui número de notificação para que seja utilizada na pesquisa.",
                    category="info",
                )
                self.reporter.error(
                    "Exame sem número de notificação. Pesquisa abortada."
                )
                self.reporter.increment_stat("exams_without_notification_number")
                return []
            criterias.extend(["Número da Notificação"])
        else:
            criterias.extend(
                [
                    k
                    for k in self.criterias.keys()
                    if self.criterias[k]["pode_usar"] and k != "Número da Notificação"
                ]
            )
            self.reporter.debug(
                f"Pesquisando utilizando os critérios: {'; '.join(criterias)}"
            )

        if "Data de Nascimento" in criterias and patient.birth_date is None:
            display(
                "Este paciente não possui data de nascimento para que seja utilizada na pesquisa.",
                category="error",
            )
            self.reporter.error(
                "Pacientente sem data de nascimento. Pesquisa abortada."
            )
            self.reporter.clean_patient()
            return []

        for criteria in criterias:
            self.add_criteria(criteria, patient)

        results = self.__treat_results(self.__search())
        results_count = len(results)

        if results_count == 0 and not use_notification_number:
            display(
                f"Utilizando os critérios {tuple(criterias)} não foram encontrados resultados para o paciente {patient.name}. Pesquisando pelo número de notificação agora.",
                category="info",
            )
            self.reporter.info(
                "Nenhuma notificação encontrada. Será feita uma nova pesquisa utilizando o número de notificação"
            )
            return self.search(
                patient, use_notification_number=True, start_time=start_time
            )

        end_time = time.time()
        elapsed_time = end_time - start_time

        if results_count > 1:
            display(
                f"Mais de um resultado encontrado ao pesquisar pelo paciente {patient.name}. Avaliando nome da mãe de cada notificação.",
                category="info",
            )
            self.reporter.info(
                "Paciente tem mais de 1 resultado de notificação. Verificando nome da mãe de cada notificação."
            )
            results = self.__check_mother_names(results)

        display(
            f"Paciente pesquisado ({patient.name}) finalizou a pesquisa em {elapsed_time:.2f} segundos. {results_count} notificações consideradas."
        )
        self.reporter.debug(
            f"Pesquisa feita em {elapsed_time:.2f} segundos. {results_count} notificações consideradas."
        )
        self.reporter.increment_stat("search_time", elapsed_time)
        self.reporter.clean_patient()
        return results

    def __treat_results(self, res: requests.Response) -> list[Sheet]:
        """This will receive the search response from the sinan website and will return a list of dicts with the results

        Args:
            res (requests.Response): The response from the sinan website

        Returns:
            list[Sheet]: A list of dicts with the results
        """
        soup = BeautifulSoup(res.content, "html.parser")
        reult_tag = soup.find("span", {"id": "form:panelResultadoPesquisa"})
        thead = valid_tag(soup.find("thead", {"class": "rich-table-thead"}))
        tbody = valid_tag(soup.find("tbody", {"id": "form:tabelaResultadoPesquisa:tb"}))

        if not (thead and tbody and reult_tag):
            return []

        column_names = [th.span.text.strip() for th in thead.find_all("th")]
        sheets: list[Sheet] = []

        for i, row in enumerate(tbody.find_all("tr"), 0):
            row_values = [td.text.strip() for td in row.find_all("td")]
            value = dict(zip(column_names, row_values))
            payload = self.base_payload.copy()

            payload.update(
                {
                    f"form:tabelaResultadoPesquisa:{i}:visualizarNotificacao": f"form:tabelaResultadoPesquisa:{i}:visualizarNotificacao"
                }
            )

            sheet = Sheet(
                self.session,
                self.municipality,
                self.patient,
                value,
                payload,
                self.reporter,
            )
            self.reporter.increment_stat("notifications")
            if sheet.is_oportunity:
                sheets.append(sheet)
                self.reporter.increment_stat("oportunity")
            else:
                self.reporter.increment_stat("not_oportunity")

        if any(
            sheet.result_municipality_notified != sheet.result_municipality_residence
            for sheet in sheets
        ):
            self.reporter.warn(
                "Uma das notificações encontradas não foi notificada pelo município. Analisando possibilidades de notificação.",
                f"Nº de Notificação das fichas para análise: {';'.join(sheet.notification_number for sheet in sheets)}",
            )
            if any(sheet.is_return_flow for sheet in sheets):
                self.reporter.warn(
                    "Uma das fichas encontradas na pesquisa já foi habilitada para fluxo de retorno. Portanto todos os resultados deste paciente será ignorado.",
                    f"Nº de Notificação das fichas ignoradas: {';'.join(sheet.notification_number for sheet in sheets)}",
                )
                return []
            elif any(sheet.is_notified_by_another_municipality for sheet in sheets):
                self.reporter.warn(
                    "Uma das fichas encontradas na pesquisa foi notificada por outro município, deve se pedir para que o município habilite para o município de residência. Portanto, todos os resultados deste paciente serão ignorados.",
                    f"Nº de Notificação das fichas ignoradas: {';'.join(sheet.notification_number for sheet in sheets)}",
                )
                return []
            elif any(sheet.is_extra_case for sheet in sheets):
                self.reporter.warn(
                    "Uma das fichas encontradas na pesquisa é de caso extra. Portanto todos os resultados deste paciente será ignorado. (CHAMAR O FELIPE)",
                    f"Nº de Notificação das fichas ignoradas: {';'.join(sheet.notification_number for sheet in sheets)}",
                )
                return []

        return sheets
