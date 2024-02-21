from typing import Literal

import requests
from bs4 import BeautifulSoup

from core.constants import CURRENT_YEAR_FIRST_DAY, SINAN_BASE_URL, TODAY
from core.utils import valid_tag


class NotificationResearcher:
    """Consult a notification given a patient name

    Args:
        session (requests.Session): Requests session logged obj
        agravo (str): Agravo to filter by (eg. A90 - DENGUE)

    Methods:
        consultar(self, patient: str): Consult a notification and return the response
    """

    def __init__(
        self, session: requests.Session, agravo: Literal["A90 - DENGUE"]
    ):
        self.session = session
        self.base_payload = {
            "AJAXREQUEST": "_viewRoot",
            "form": "form",
            "form:consulta_tipoPeriodo": "0",
            "form:consulta_dataInicialInputDate": CURRENT_YEAR_FIRST_DAY.strftime(
                "%d/%m/%Y"
            ),
            "form:consulta_dataInicialInputCurrentDate": TODAY.strftime(
                "%m/%Y"
            ),
            "form:consulta_dataFinalInputDate": TODAY.strftime("%d/%m/%Y"),
            "form:consulta_dataFinalInputCurrentDate": TODAY.strftime("%m/%Y"),
            "form:richagravocomboboxField": agravo,
            "form:richagravo": agravo,
            "form:tipoUf": "3",  # Notificação ou Residência
            "form:consulta_uf": "24",  # SC
            "form:tipoSaida": "2",  # Lista de Notificação
            "form:consulta_tipoCampo": "0",
            "form:consulta_municipio_uf_id": "0",
            "form:j_id161": "Selecione valor no campo",
        }
        self.endpoint = (
            f"{SINAN_BASE_URL}/sinan/secured/consultar/consultarNotificacao.jsf"
        )

    def __selecionar_agravo(self):
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:j_id108": "form:j_id108",
                "AJAX:EVENTS_COUNT": "1",
            }
        )
        self.session.post(self.endpoint, data=payload)

    def __adicionar_criterio(self):
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": "13",
                "form:consulta_operador": "2",
                "form:consulta_municipio_uf_id": "0",
                "form:consulta_dsTextoPesquisa": self.paciente,
                "form:btnAdicionarCriterio": "form:btnAdicionarCriterio",
            }
        )
        payload.pop("form:j_id161", None)
        self.session.post(self.endpoint, data=payload)

    def __selecionar_criterio_campo(self):
        CRITERIO = "Nome do paciente"

        options = self.soup.find("select", {"id": "form:consulta_tipoCampo"}).find_all("option")  # type: ignore
        tipo_campo = next(
            (option for option in options if option.text.strip() == CRITERIO),
            None,
        )

        if not tipo_campo:
            print(f"Criterio {CRITERIO} not found.")
            exit(1)

        payload = self.base_payload.copy()
        payload.update(
            {
                "form:consulta_tipoCampo": tipo_campo.get("value"),
                "form:j_id136": "form:j_id136",
                "ajaxSingle": "form:consulta_tipoCampo",
            }
        )
        self.session.post(self.endpoint, data=payload)

        self.__adicionar_criterio()

    def __pesquisar(self):
        payload = self.base_payload.copy()
        payload.update(
            {
                "form:btnPesquisar": "form:btnPesquisar",
            }
        )
        res = self.session.post(self.endpoint, data=payload)
        return res

    def search(self, patient_name: str):
        """Search for a patient in the Sinan website (Consultar Notificação)

        Args:
            patient_name (str): The name of the patient

        Returns:
            List[dict]: A list of dicts with the results and each dict has the key
                `open_payload` with the payload to open the patient's investigation page
        """
        self.paciente = patient_name

        res = self.session.get(self.endpoint)
        self.soup = BeautifulSoup(res.content, "html.parser")
        javax_faces = valid_tag(
            self.soup.find("input", {"name": "javax.faces.ViewState"})
        )
        if not javax_faces:
            print("Java Faces not found.")
            exit(1)

        self.base_payload["javax.faces.ViewState"] = javax_faces.get("value")  # type: ignore

        self.__selecionar_agravo()
        self.__selecionar_criterio_campo()
        res = self.__pesquisar()
        return self.tratar_resultado(res)

    def tratar_resultado(self, res: requests.Response) -> list[dict]:
        """This will receive the search response from the sinan website and will return a list of dicts with the results

        Args:
            res (requests.Response): The response from the sinan website

        Returns:
            list[dict]: A list of dicts with the results
        """
        soup = BeautifulSoup(res.content, "html.parser")
        reult_tag = soup.find("span", {"id": "form:panelResultadoPesquisa"})
        thead = valid_tag(soup.find("thead", {"class": "rich-table-thead"}))
        tbody = valid_tag(
            soup.find("tbody", {"id": "form:tabelaResultadoPesquisa:tb"})
        )

        # not all([thead, tbody, reult_tag]):
        if not (thead and tbody and reult_tag):
            return []

        column_names = [th.span.text.strip() for th in thead.find_all("th")]
        values = []

        for row in tbody.find_all("tr"):
            row_values = [td.text.strip() for td in row.find_all("td")]
            value = dict(zip(column_names, row_values))
            payload = self.base_payload.copy()
            # keys2remove = ["AJAXREQUEST"]

            payload.update(
                {
                    "form:tabelaResultadoPesquisa:0:visualizarNotificacao": "form:tabelaResultadoPesquisa:0:visualizarNotificacao"
                }
            )

            value.update(open_payload=payload)
            values.append(value)

        return values
