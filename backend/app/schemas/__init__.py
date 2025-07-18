from .client import Client, ClientCreate, ClientUpdate
from .message import Message, MessageCreate, MessageUpdate, SenderType
from .dossier import Dossier, DossierCreate, DossierUpdate

__all__ = [
    "Client", "ClientCreate", "ClientUpdate",
    "Message", "MessageCreate", "MessageUpdate", "SenderType",
    "Dossier", "DossierCreate", "DossierUpdate"
]