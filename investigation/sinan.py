import requests
from bs4 import BeautifulSoup

from core.abstract import Bot
from core.constants import SINAN_BASE_URL, USER_AGENT
from core.utils import Printter, valid_tag
from investigation.data_loader import SinanGalData
from investigation.investigator import DuplicateChecker
from investigation.notification_researcher import NotificationResearcher
from investigation.patient import Patient
from investigation.report import Report

display = Printter("SINAN")


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
        # self.reporter._example()  # Just for testing purposes

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
        municipality = self._settings["sinan_investigacao"]["municipio"]
        self.researcher = NotificationResearcher(
            self.session, agravo, municipality, criterios, self.reporter
        )

    def __create_duplicate_checker(self):
        """Create a duplicate checker instance that will be used to analyze duplicates"""
        self.duplicate_checker = DuplicateChecker(self.session, self.reporter)

    def _init_apps(self):
        """Factory method to initialize the apps"""
        initializators = [
            self.__create_session,
            self.__create_notification_researcher,
            self.__create_duplicate_checker,
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
            display("Falha au tentar logar. Verique as credenciais.")
            exit(1)

        # update the apps that use the session
        need_session = [self.researcher, self.duplicate_checker]
        for app in need_session:
            setattr(app, "session", self.session)

    def _login(self):
        """Login to the Sinan Website"""
        display("Fazendo login utilizando as credenciais fornecidas...")

        # set JSESSIONID
        res = self.session.get(f"{SINAN_BASE_URL}/sinan/login/login.jsf")

        soup = BeautifulSoup(res.content, "html.parser")
        form = valid_tag(soup.find("form"))
        if not form:
            display(
                "Erro: Nenhum formulário encontrado. (pode ser que o site tenha atualizado)"
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
        display("Login efetuado com sucesso!")

    def __fill_form(self, patient: Patient):
        """Fill out the form with the patient data

        Args:
            patient (Patient): The patient data
        """
        sheets = self.researcher.search(patient)

        self.reporter.set_patient(patient)
        match len(sheets):
            case 0:
                display(f"Nenhum resultado encontrado para {patient.name}. Ignorado.")
                self.reporter.warn("Paciente ignorado por não ter nenhum resultado")
            case 1:
                display(
                    f"Preechendo investigação do resultado encontrado para {patient.name}."
                )
                sheet = next(iter(sheets))
                sheet.investigate_patient()
            case _:
                display(f"Múltiplos resultados encontrados para {patient.name}.")
                self.reporter.warn("Paciente tem mais de 1 resultado (duplicidade).")
                self.duplicate_checker.investigate_multiple(patient, sheets)

    def start(self):
        self._login()
        total = len(self.data.df)
        for i, patient in self.data.df.iterrows():
            i += 1  # type: ignore [fé]
            patient = Patient(patient.to_dict())
            display(
                f"[{i} de {total}] Preenchendo investigação do paciente {patient.name}..."
            )
            self.__fill_form(patient)
            print("\n" + "*" * 25, end="\n")
            # input("Pressione Enter para prosseguir para o próximo paciente.")
