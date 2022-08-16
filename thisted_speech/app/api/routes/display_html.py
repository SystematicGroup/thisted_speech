import os

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from thisted_speech.app.core.config import PROJECT_ROOT

router = APIRouter()

from loguru import logger


@router.get("/", response_class=HTMLResponse)
def get_hearbeat() -> HTMLResponse:
    logger.info(os.getcwd())
    with open(os.path.join(PROJECT_ROOT, "demofile.html"), "r") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content, status_code=200)
