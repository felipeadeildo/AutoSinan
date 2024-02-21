import datetime as dt

SINAN_BASE_URL = "http://sinan.saude.gov.br"  # protocol http
"""Base url for Sinan Website."""

TODAY = dt.datetime.now()
"""Datetime object for today."""

CURRENT_YEAR_FIRST_DAY = dt.date(year=TODAY.year, month=1, day=1)
"""Date object for the first day of the current year."""


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)
"""User agent string used to access the website"""


CREDENTIALS_FILE = "credentials.json"
"""Credentials file name with the credentials to access the website"""


DATA_FOLDER = "dados"
"""Folder name to store the datasets used by the bots."""
