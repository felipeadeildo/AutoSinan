from typing import List

import requests

from investigation.patient import Patient
from investigation.report import Report
from investigation.sheet import Sheet


class NotFoundError(Exception):
    """Raised when something in the page was not found."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DuplicateChecker:
    """Given a patient data and your payload to open the Sinan page, this class will be used to investigate the patient."""

    def __init__(self, session: requests.Session, reporter: Report) -> None:
        self.session = session
        self.reporter = reporter

    def __compare_investigations(self, episode: List[Sheet]):
        """Compare investigatio result and select the ones that will be considered

        Args:
            episode (List[Sheet]): List of notifications of one episode that has investigation.
        """
        episode_sorted = list(
            sorted(
                episode,
                key=lambda episode: (episode.priority, episode.notification_date),
                reverse=True,
            )
        )

        return episode_sorted[:1], episode_sorted[1:]

    def __investigate_episode(self, episode: List[Sheet]):
        """Compare all the sheets (results) and define what will be considered and what will be discarded

        As defined in the Google Doc document:
            1. Every notifications does not have a investigation: Consider only the oldest notification and discard the rest
            2. Every result has investigation: Compare all investigation as defined in the Google Doc
            3. Some resuls has investigation and other does not: Consider only the notification with investigation and discard the rest

        Args:
            episode (List[Sheet]): The list os sheets of one episode.
        """
        considered: List[Sheet] = []
        discarded: List[Sheet] = []

        # 1. Every notifications does not have a investigation: Consider only the oldest notification and discard the rest
        if not all(sheet.has_previous_investigation for sheet in episode):
            self.reporter.warn(
                "Todas as notificações do episódio avaliado NÃO possuem ficha de investigação, portanto será considerado apenas a última notificação e o resto será excluído."
            )
            considered.append(episode[0])
            discarded.extend(episode[1:])
        # 2. Every result has investigation: Compare all investigation as defined in the Google Doc
        elif all(sheet.has_previous_investigation for sheet in episode):
            self.reporter.warn(
                "Todas as notificações do episódio avaliado POSSUEM ficha de investigação, portanto será avaliado o conteúdo de cada investigação para decidir quais serão excluídas e qual ficará."
            )
            considered, discarded = self.__compare_investigations(episode)

        # 3. Some resuls has investigation and other does not: Consider only the notifications with investigation and discard the rest
        else:
            self.reporter.warn(
                "Algumas notificações desse episódio possuem ficha de investigação e outras não, portanto as fichas de notificação que possui ficha de investigação serão consideradas numa nova análise de duplicidade enquanto que o resto será excluído."
            )
            considered.extend(
                [sheet for sheet in episode if sheet.has_previous_investigation]
            )
            discarded.extend(
                [sheet for sheet in episode if not sheet.has_previous_investigation]
            )

        if len(considered) > 1:
            self.reporter.info(
                "Como houveram mais de uma ficha de notificação considerada, o algorítimo de análise de duplicidade será aplicado novamente.",
                f"{len(considered)} notificações consideradas. ({';'.join(sheet.notification_number for sheet in considered)})",
            )
            self.__investigate_episode(considered)
        else:
            for sheet in considered:
                sheet.investigate_patient()

        for sheet in discarded:
            sheet.delete()

    def investigate_multiple(self, patient: Patient, sheets: List[Sheet]):
        """Investigate multiple patients filling out the patient data on the Sinan Investigation page

        Args:
            patient (Patient): The patient to be investigated
            sheets (List[Sheet]): The list of sheets to be duplicity-analyzed
        """

        # 1. Dado vários resultados, eu tenho que fazer a lódica de "episódios"
        episodes: List[List[Sheet]] = []

        sheets.sort(key=lambda x: x.notification_date)

        # The first episode starts with the first oportunity resut
        episodes.append([sheets[0]])

        for sheet in sheets[1:]:
            # the current sheet diffs more than 15 days from the last episode
            if (sheet.notification_date - episodes[-1][0].notification_date).days > 15:
                episodes.append([sheet])
            else:
                episodes[-1].append(sheet)

        self.reporter.set_patient(patient)
        if patient.exam_type == "IgM":
            if patient.exam_result == "Não Reagente":
                # TODO: 90 days before the collection date (????, idk)
                self.reporter.warn(
                    "O exame é do tipo IgM e o resultado é Não Reagente, portanto todos episódios serão encerrados como descartados (se não houver classificação prévia).",
                    f"Quantidade de episódios encontrados: {len(episodes)}",
                )
                for episode in episodes:
                    for sheet in episode:
                        sheet.investigate_patient()
            else:
                self.reporter.warn(
                    f"O exame é do tipo IgM e o resultado é {patient.exam_result}, portanto somente o último episódio será encerrado deixando os demais em branco.",
                    f"Quantidade de episódios encontrados: {len(episodes)}",
                )
                for sheet in episodes[-1]:
                    sheet.investigate_patient()
        else:
            if len(episodes) > 1:
                self.reporter.error(
                    "A pesquisa retornou vários resultados que por sua vez gerou mais de um episódio. O bot não sabe o que fazer nesta situação.",
                    "Matrix Error kk",
                )
                return
            self.__investigate_episode(episodes[0])
