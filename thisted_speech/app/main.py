import os

from fastapi import FastAPI

from thisted_speech.app.api.routes.router import api_router
from thisted_speech.app.core.config import (API_PREFIX, APP_NAME, APP_VERSION, IS_DEBUG)
from thisted_speech.app.core.event_handlers import (start_app_handler, stop_app_handler)


def get_app() -> FastAPI:
    fast_app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=IS_DEBUG)
    fast_app.include_router(api_router, prefix=API_PREFIX)

    fast_app.add_event_handler("startup", start_app_handler(fast_app))
    fast_app.add_event_handler("shutdown", stop_app_handler(fast_app))

    return fast_app


app = get_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
