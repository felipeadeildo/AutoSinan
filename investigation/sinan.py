import requests
from bs4 import BeautifulSoup

from core.abstract import Bot
from core.constants import SINAN_BASE_URL, USER_AGENT
from core.utils import valid_tag
from investigation.data_loader import SinanGalData
from investigation.investigator import Investigator
from investigation.notification_researcher import NotificationResearcher
from investigation.report import Report


class InvestigationBot(Bot):
    """Sinan client taht will be used to interact with the Sinan Website doing things like:
    - Login
    - Filling out forms
    - Verifying submitted forms
    """

    def __init__(self, settings: dict) -> None:
        self._username = settings["sinan_credentials"]["username"]
        self._password = settings["sinan_credentials"]["password"]
        self._settings = settings
        self.reporter = Report()

        self._init_apps()

    def __create_data_manager(self):
        """Load data from SINAN and GAL datasets"""
        self.data = SinanGalData(self._settings, self.reporter)
        self.data.load()
        self.reporter.generate_reports_filename(self.data.df)

    def __create_session(self):
        """Create a session agent that will be used to make requests"""
        self.session = requests.session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def __create_notification_researcher(self):
        """Create a notification searcher that will be used to research notifications given a patient"""
        agravo = self._settings["sinan_investigacao"]["agravo"]
        criterios = self._settings["sinan_investigacao"]["criterios"]
        self.researcher = NotificationResearcher(
            self.session, agravo, criterios, self.reporter
        )

    def __create_investigator(self):
        """Create an Investigator that will be used to investigate (fill data)"""
        self.investigator = Investigator(self.session, self.reporter)

    def _init_apps(self):
        """Factory method to initialize the apps"""
        initializators = [
            self.__create_session,
            self.__create_notification_researcher,
            self.__create_investigator,
            self.__create_data_manager,
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
            print("[SINAN] Falha au tentar logar. Verique as credenciais.")
            exit(1)

        # update the apps that use the session
        need_session = [self.researcher, self.investigator]
        for app in need_session:
            setattr(app, "session", self.session)

    def _login(self):
        """Login to the Sinan Website"""
        print("[SINAN] Fazendo login utilizando as credenciais fornecidas...")

        # set JSESSIONID
        res = self.session.get(f"{SINAN_BASE_URL}/sinan/login/login.jsf")

        soup = BeautifulSoup(res.content, "html.parser")
        form = valid_tag(soup.find("form"))
        if not form:
            print(
                "[SINAN] Erro: Nenhum formulário encontrado. (pode ser que o site tenha atualizado)"
            )
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
        print("[SINAN] Login efetuado com sucesso!")

    def __fill_form(self, patient: dict):
        """Fill out the form with the patient data

        Args:
            patient (dict): The patient data
        """
        sinan_response = self.researcher.search(patient)
        open_payloads = [r["open_payload"] for r in sinan_response]

        self.reporter.set_patient(patient)
        match len(sinan_response):
            case 0:
                print(
                    f"[SINAN] Nenhum resultado encontrado para {patient['Paciente']}. Ignorado."
                )
                self.reporter.warn("Paciente ignorado por não ter nenhum resultado")
            case 1:
                print(
                    f"[SINAN] Preechendo investigação do resultado encontrado para {patient['Paciente']}."
                )
                open_payload = next(iter(open_payloads))
                self.investigator.investigate(patient, open_payload)
            case _:
                print(
                    f"[SINAN] Múltiplos resultados encontrados para {patient['Paciente']}."
                )
                self.reporter.warn("Paciente tem mais de 1 resultado.")
                self.investigator.investigate_multiple(patient, open_payloads)

    def start(self):
        self._login()
        total = len(self.data.df)
        for i, patient in self.data.df.iterrows():
            i += 1  # type: ignore [fé]
            print(
                f"\n[SINAN] [{i} de {total}] Preenchendo investigação do paciente {patient['Paciente']}..."
            )
            self.__fill_form(patient.to_dict())
            print("\n" + "*" * 25, end="\n")
