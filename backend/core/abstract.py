from abc import ABC, abstractmethod


class Bot(ABC):
    """Abstract Bot representation"""

    def __init__(self, settings: dict):
        """Initialize Bot with the settings including the Sinan credentials

        Args:
            settings (dict): Configuration
        """
        raise NotImplementedError("init() not implemented")

    @abstractmethod
    def start(self):
        """Starts the bot execution with your own logic"""
        raise NotImplementedError("start() not implemented")
