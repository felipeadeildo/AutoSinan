import logging

import requests
from bs4 import BeautifulSoup

from core.constants import POSSIBLE_AGRAVOS, SEARCH_POSSIBLE_CRITERIAS, SINAN_BASE_URL
from core.utils import generate_search_base_payload, valid_tag


class Criterias:
    """Criterias of notification research methods to improve the research filters"""

    def __init__(
        self,
        session: requests.Session,
        criterias: dict,
        logger: logging.Logger,
        endpoint: str,
        base_payload: dict,
    ):
        self.session = session
        self.logger = logger
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
        self, patient_data: dict, field_type_id: str, operator: str
    ):
        """Send the payload to select the patient name criteria on search"""

        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": field_type_id,
                "form:consulta_operador": operator,
                "form:consulta_dsTextoPesquisa": patient_data["Paciente"],
                "form:consulta_municipio_uf_id": "0",  # Exemplos que tive isso sempre estava desabilitado.
                "form:btnAdicionarCriterio": "form:btnAdicionarCriterio",
            }
        )

        self.session.post(self.endpoint, data=payload)
        self.current_criterias.append("Nome do paciente")

    def __patient_notification_criteria(
        self, patient_data: dict, field_type_id: str, operator: str
    ):
        """Send the payload to select the patient notification number criteria on search"""
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta.tipoCampo": field_type_id,
                "form:consulta_operador": operator,
                "form:consulta_dsTextoPesquisa": patient_data["Núm. Notificação Sinan"],
                "form:consulta_municipio_uf_id": "0",  # Exemplos que tive isso sempre estava desabilitado.
                "form:btnAdicionarCriterio": "form:btnAdicionarCriterio",
            }
        )
        self.session.post(self.endpoint, data=payload)
        self.current_criterias.append("Número da Notificação")

    def __patient_date_of_birth_criteria(
        self, patient_data: dict, field_type_id: str, operator: str
    ):
        """Send the payload to select the patient date of birth criteria on search"""
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta.tipoCampo": field_type_id,
                "form:consulta_operador": operator,
                "form:consulta_dsTextoPesquisa": patient_data["Data de Nascimento"],
                "form:consulta_municipio_uf_id": "0",  # Exemplos que tive isso sempre estava desabilitado.
                "form:btnAdicionarCriterio": "form:btnAdicionarCriterio",
            }
        )

        self.session.post(self.endpoint, data=payload)
        self.current_criterias.append("Data de nascimento")

    def __patient_mother_name_criteria(
        self, patient_data: dict, field_type_id: str, operator: str
    ):
        """Send the payload to select the patient month name criteria on search"""
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta.tipoCampo": field_type_id,
                "form:consulta_operador": operator,
                "form:consulta_dsTextoPesquisa": patient_data["Nome da Mãe"],
                "form:consulta_municipio_uf_id": "0",  # Exemplos que tive isso sempre estava desabilitado.
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
            self.logger.error(f"Criteria {criteria} not found.")
            print(f"Criteria {criteria} not found.")
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
        ).find_all("option")  # type: ignore [fé]
        operators = {tag.get_text(): tag.get("value") for tag in operator_options}
        return field_type_value, operators

    def add_criteria(
        self,
        criteria: SEARCH_POSSIBLE_CRITERIAS,
        patient_data: dict,
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

        criterias[criteria](patient_data, field_type_id, operator)


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
        criterias: dict,
        logger: logging.Logger,
    ):
        endpoint = f"{SINAN_BASE_URL}/sinan/secured/consultar/consultarNotificacao.jsf"
        base_payload = generate_search_base_payload(agravo)

        super().__init__(
            session,
            criterias,
            logger,
            endpoint,
            base_payload,
        )

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
        """Loads ednpoint page and extract the javax.faces.ViewState this session"""
        res = self.session.get(self.endpoint)
        self.soup = BeautifulSoup(res.content, "html.parser")
        javax_faces = valid_tag(
            self.soup.find("input", {"name": "javax.faces.ViewState"})
        )
        if not javax_faces:
            self.logger.error("Java Faces not found.")
            print("Java Faces not found.")
            exit(1)

        self.base_payload["javax.faces.ViewState"] = javax_faces.get("value")  # type: ignore

    def search(self, patient: dict, use_notification_number: bool = False):
        """Search for a patient in the Sinan website (Consultar Notificação)

        Args:
            patient (dict): The patient data from GAL to search

        Returns:
            List[dict]: A list of dicts with the results and each dict has the key
                `open_payload` with the payload to open the patient's investigation page
        """
        self.logger.info(
            "NOTIFICATION_RESEARCHER: Pesquisando pelo paciente: %s",
            patient["Paciente"],
        )
        self.paciente = patient
        self.__define_javax_faces()
        self.__select_agravo()

        criterias: list[SEARCH_POSSIBLE_CRITERIAS] = []
        if use_notification_number:
            criterias.extend(["Número da Notificação"])
        else:
            criterias.extend(
                [
                    k
                    for k in self.criterias.keys()
                    if k != "Número da Notificação" and self.criterias[k]["deve_usar"]
                ]
            )

        for criteria in criterias:
            self.add_criteria(criteria, patient)

        results = self.treat_results(self.__search())

        if len(results) == 0:
            self.logger.warning(
                f"NOTIFICATION_RESEARCHER: Utilizando os critérios {tuple(criterias)} não foram encontrados pacientes para o paciente {patient['Paciente']}. Pesquisando pelo número de notificação agora."
            )
            return self.search(patient, use_notification_number=True)

        self.logger.info(
            "NOTIFICATION_RESEARCHER: Paciente pesquisado (%s) teve %d notificações encontradas no Sinan Online",
            patient["Paciente"],
            len(results),
        )
        return results

    def treat_results(self, res: requests.Response) -> list[dict]:
        """This will receive the search response from the sinan website and will return a list of dicts with the results

        Args:
            res (requests.Response): The response from the sinan website

        Returns:
            list[dict]: A list of dicts with the results
        """
        soup = BeautifulSoup(res.content, "html.parser")
        reult_tag = soup.find("span", {"id": "form:panelResultadoPesquisa"})
        thead = valid_tag(soup.find("thead", {"class": "rich-table-thead"}))
        tbody = valid_tag(soup.find("tbody", {"id": "form:tabelaResultadoPesquisa:tb"}))

        # not all([thead, tbody, reult_tag]):
        if not (thead and tbody and reult_tag):
            return []

        column_names = [th.span.text.strip() for th in thead.find_all("th")]
        values = []

        for i, row in enumerate(tbody.find_all("tr"), 0):
            row_values = [td.text.strip() for td in row.find_all("td")]
            value = dict(zip(column_names, row_values))
            payload = self.base_payload.copy()
            # keys2remove = ["AJAXREQUEST"]

            payload.update(
                {
                    f"form:tabelaResultadoPesquisa:{i}:visualizarNotificacao": f"form:tabelaResultadoPesquisa:{i}:visualizarNotificacao"
                }
            )

            value.update(open_payload=payload)
            values.append(value)

        return values
        return values
