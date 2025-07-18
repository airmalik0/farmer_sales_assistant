from fastapi import APIRouter
from .clients import router as clients_router
from .messages import router as messages_router
from .dossier import router as dossier_router
from .websocket import router as websocket_router
from .telegram import router as telegram_router

api_router = APIRouter()

api_router.include_router(clients_router, prefix="/clients", tags=["clients"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
api_router.include_router(dossier_router, prefix="/dossier", tags=["dossier"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])
api_router.include_router(telegram_router, prefix="/telegram", tags=["telegram"])