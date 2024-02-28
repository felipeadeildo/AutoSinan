import pandas as pd
import requests
from bs4 import BeautifulSoup

from core.abstract import Bot
from core.constants import SINAN_BASE_URL, USER_AGENT
from core.utils import valid_tag
from investigation.data_loader import SinanGalData
from investigation.investigator import Investigator
from investigation.notification_researcher import NotificationResearcher


class InvestigationBot(Bot):
    """Sinan client taht will be used to interact with the Sinan Website doing things like:
    - Login
    - Filling out forms
    - Verifying submitted forms
    """

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

        self._init_apps()

    def __create_data_manager(self):
        """Load data from SINAN and GAL datasets"""
        self.data = SinanGalData()
        self.data.load()
        # self.data.df.to_excel("base_unificada.xlsx", index=False)

    def __create_session(self):
        """Create a session agent that will be used to make requests"""
        self.session = requests.session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def __create_notification_researcher(self):
        """Create a notification searcher that will be used to research notifications given a patient"""
        # TODO: move the agravo to a settings.toml file
        self.researcher = NotificationResearcher(self.session, "A90 - DENGUE")

    def __create_investigator(self):
        """Create an Investigator that will be used to investigate (fill data)"""
        self.investigator = Investigator(self.session)

    def _init_apps(self):
        """Factory method to initialize the apps"""
        initializators = [
            self.__create_session,
            self.__create_notification_researcher,
            self.__create_investigator,
            # self.__create_data_manager,
        ]

        for fn in initializators:
            fn()

    def __verify_login(self, res: requests.Response):
        """Verify if the login was successful

        Args:
            res (requests.Response): The response from the sinan website
        """
        soup = BeautifulSoup(res.content, "html.parser")
        if not soup.find("div", {"id": "detalheUsuario"}):
            print("Login failed.")
            exit(1)

        # update the apps that use the session
        need_session = [self.researcher, self.investigator]
        for app in need_session:
            setattr(app, "session", self.session)

    def _login(self):
        """Login to the Sinan Website"""
        print("Logando no SINAN...")
        self.__create_session()

        # set JSESSIONID
        res = self.session.get(f"{SINAN_BASE_URL}/sinan/login/login.jsf")

        soup = BeautifulSoup(res.content, "html.parser")
        form = valid_tag(soup.find("form"))
        if not form:
            print("Login Form not found.")
            exit(1)

        inputs = form.find_all("input")
        payload = dict()
        for input_ in inputs:
            name, value = input_.get("name"), input_.get("value")
            if "username" in name:
                value = self._username
            elif "password" in name:
                value = self._password
            payload[name] = value

        res = self.session.post(
            f"{SINAN_BASE_URL}{form.get('action')}",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.__verify_login(res)
        print("Logado com sucesso.")

    def __fill_form(self, patient: pd.Series):
        """Fill out the form with the patient data

        Args:
            patient (dict): The patient data
        """
        print("Paciente:", patient["NM_PACIENT"])
        sinan_response = self.researcher.search(patient["NM_PACIENT"])
        match len(sinan_response):
            case 0:
                print("Nenhum resultado encontrado.")
            case 1:
                sinan_response = next(iter(sinan_response))  # type: ignore
                self.investigator.investigate(patient.to_dict(), sinan_response)
            case _:
                print("Múltiplos resultados encontrados!")

    def start(self):
        self._login()

        # TODO: remove this after, its for testing
        # df = pd.read_excel("base_unificada.xlsx")
        # patient = df.loc[df["NM_PACIENT"] == "AIN"]
        # self.__fill_form(patient.iloc[0])

        for _, patient in self.data.df.iterrows():
            self.__fill_form(patient)
