from fastapi import APIRouter
from starlette.requests import Request
from loguru import logger

from thisted_speech.app.payloads.totext import ToTextResult, StopPayload
from thisted_speech.app.services.models import ToTextModel
from thisted_speech.models import totext_service

router = APIRouter()


@router.post("/start", response_model=None, name="start")
def post_speech_start(request: Request) -> None:
    model: ToTextModel = request.app.state.current_state
    totext_service.open_stream(model.current_state)


@router.post("/next", response_model=ToTextResult, name="next")
def post_speech_next(request: Request) -> ToTextResult:
    model: ToTextModel = request.app.state.current_state
    return model.get_next()


@router.post("/stop", response_model=None, name="stop")
def post_speech_stop(user_name: str, request: Request) -> None:

    logger.info(user_name)
    model: ToTextModel = request.app.state.current_state
    totext_service.close_stream(model.current_state, user_name)

