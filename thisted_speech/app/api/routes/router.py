from fastapi import APIRouter

from thisted_speech.app.api.routes import heartbeat, totext, display_html, tospeech

api_router = APIRouter()
api_router.include_router(heartbeat.router, tags=["health"], prefix="/health")
api_router.include_router(totext.router, tags=[], prefix="/totext")

api_router.include_router(display_html.router)
