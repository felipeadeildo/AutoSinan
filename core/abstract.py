from abc import ABC, abstractmethod


class Bot(ABC):
    """Abstract Bot representation"""

    def __init__(self, username: str, password: str):
        """Initialize Bot with the Sinan Credentials

        Args:
            username (str): Sinan Username
            password (str): Sinan Password
        """
        self.username = username
        self.password = password

    @abstractmethod
    def start(self):
        """Starts the bot execution with your own logic"""
        raise NotImplementedError("start() not implemented")
