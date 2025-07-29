from .client import Client, ClientCreate, ClientUpdate
from .message import Message, MessageCreate, MessageUpdate, SenderType
from .dossier import Dossier, DossierCreate, DossierUpdate, DossierManualUpdate
from .car_interest import CarInterest, CarInterestCreate, CarInterestUpdate, CarInterestManualUpdate, CarQueryManualUpdate
from .task import Task, TaskCreate, TaskUpdate, TaskManualUpdate
from .trigger import (
    Trigger, TriggerCreate, TriggerUpdate, TriggerSummary,
    TriggerLog, TriggerLogCreate, TriggerConditions,
    NotifyActionConfig, CreateTaskActionConfig, WebhookActionConfig
)

__all__ = [
    "Client", "ClientCreate", "ClientUpdate",
    "Message", "MessageCreate", "MessageUpdate", "SenderType",
    "Dossier", "DossierCreate", "DossierUpdate", "DossierManualUpdate",
    "CarInterest", "CarInterestCreate", "CarInterestUpdate", "CarInterestManualUpdate", "CarQueryManualUpdate",
    "Task", "TaskCreate", "TaskUpdate", "TaskManualUpdate",
    "Trigger", "TriggerCreate", "TriggerUpdate", "TriggerSummary",
    "TriggerLog", "TriggerLogCreate", "TriggerConditions",
    "NotifyActionConfig", "CreateTaskActionConfig", "WebhookActionConfig"
]

# Resolve forward references for Pydantic v2
Client.model_rebuild()
Dossier.model_rebuild()
CarInterest.model_rebuild()