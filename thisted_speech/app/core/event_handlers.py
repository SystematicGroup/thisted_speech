from typing import Callable

from fastapi import FastAPI
from loguru import logger

from thisted_speech.app.services.models import ToTextModel


def _startup_model(app: FastAPI) -> None:
    app.state.current_state = ToTextModel()


def _shutdown_model(app: FastAPI) -> None:
    app.state.current_state = None


def start_app_handler(app: FastAPI) -> Callable:
    def startup() -> None:
        logger.info("Running app start handler.")
        _startup_model(app)
    return startup


def stop_app_handler(app: FastAPI) -> Callable:
    def shutdown() -> None:
        logger.info("Running app shutdown handler.")
        _shutdown_model(app)
    return shutdown
