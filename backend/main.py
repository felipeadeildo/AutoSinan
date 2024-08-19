from core.abstract import Bot
from core.utils import clear_screen, get_settings
from investigation import InvestigationBot

# from notification import NotificationBot


if __name__ == "__main__":
    clear_screen()
    settings = get_settings()
    bots: dict[str, type[Bot]] = {
        "Bot de Investigação": InvestigationBot
        # "Bot de Notificação": NotificationBot
    }

    for i, opt in enumerate(bots.keys(), 1):
        print(f"{i} - {opt}")

    choice = int(input("Qual bot deseja executar? "))
    bot = bots[list(bots.keys())[choice - 1]]
    bot(settings).start()
