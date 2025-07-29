from fastapi import APIRouter
from .clients import router as clients_router
from .messages import router as messages_router
from .dossier import router as dossier_router
from .car_interest import router as car_interest_router
from .task import router as task_router
from .websocket import router as websocket_router
from .telegram import router as telegram_router
from .settings import router as settings_router
from .trigger import router as triggers_router
from .task_trigger import router as task_triggers_router

api_router = APIRouter()

api_router.include_router(clients_router, prefix="/clients", tags=["clients"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
api_router.include_router(dossier_router, prefix="/dossier", tags=["dossier"])
api_router.include_router(car_interest_router, prefix="/car_interest", tags=["car_interest"])
api_router.include_router(task_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])
api_router.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(triggers_router, prefix="/triggers", tags=["triggers"])
api_router.include_router(task_triggers_router, prefix="/task-triggers", tags=["task-triggers"])