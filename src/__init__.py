import os

from dotenv import load_dotenv

from src.configs.logging import setup_logging

# Support custom .env file path — set by the GigaIDE plugin via
# the SPYDR_DOTENV_PATH environment variable.  When unset,
# load_dotenv() looks for .env in the current working directory.
_dotenv_path = os.getenv("SPYDR_DOTENV_PATH") or None
load_dotenv(dotenv_path=_dotenv_path)
setup_logging()
