import os

from starlette.config import Config

APP_VERSION = "0.0.1"
APP_NAME = "Thisted - Speech API"
API_PREFIX = "/api"

config = Config(".env")

IS_DEBUG: bool = config("IS_DEBUG", cast=bool, default=False)

apath = os.path.dirname(__file__)
apath = os.path.abspath(os.path.join(apath, "..", "..", ".."))
PROJECT_ROOT = apath
print("PROOT", PROJECT_ROOT)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f'{PROJECT_ROOT}/text2speech-cred.json'

INPUT_FILENAME = None
