from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from ..models.client import Client
from ..schemas.client import ClientCreate, ClientUpdate
from ..core.config import settings


class ClientService:
    @staticmethod
    def get_client(db: Session, client_id: int) -> Optional[Client]:
        return db.query(Client).options(
            joinedload(Client.messages),
            joinedload(Client.dossier),
            joinedload(Client.car_interest),
            joinedload(Client.tasks)
        ).filter(Client.id == client_id).first()

    @staticmethod
    def find_client_by_pact_conversation(db: Session, conversation_id: int) -> Optional[Client]:
        """Найти клиента по Pact conversation_id"""
        return db.query(Client).options(
            joinedload(Client.messages),
            joinedload(Client.dossier),
            joinedload(Client.car_interest),
            joinedload(Client.tasks)
        ).filter(Client.pact_conversation_id == conversation_id).first()

    @staticmethod
    def find_client_by_external_id(db: Session, external_id: str, provider: str) -> Optional[Client]:
        """Найти клиента по external_id и провайдеру"""
        return db.query(Client).filter(
            Client.sender_external_id == external_id,
            Client.provider == provider
        ).first()

    @staticmethod
    def get_clients(db: Session, skip: int = 0, limit: int = 100) -> List[Client]:
        return db.query(Client).options(
            joinedload(Client.messages),
            joinedload(Client.dossier),
            joinedload(Client.car_interest),
            joinedload(Client.tasks)
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_clients_by_provider(db: Session, provider: str) -> List[Client]:
        """Получить клиентов по провайдеру"""
        return db.query(Client).filter(Client.provider == provider).all()

    @staticmethod
    def get_approved_clients(db: Session) -> List[Client]:
        """Получить клиентов с одобренными именами для рассылки"""
        return db.query(Client).filter(Client.name_approved == True).all()

    @staticmethod
    def create_client_from_pact_conversation(db: Session, conversation_data: Dict) -> Client:
        """Создать клиента из данных беседы Pact"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Создание клиента из данных: {conversation_data}")
        
        # Реальная структура Pact webhook использует прямые поля в объекте
        # conversation_id приходит как 'id' в объекте
        
        # Извлекаем данные провайдера
        provider = conversation_data.get("provider", "unknown")
        
        # Определяем контактные данные в зависимости от провайдера
        phone_number = conversation_data.get("sender_phone")
        username = None
        name = conversation_data.get("sender_name", "")
        
        # Для Telegram может быть username вместо телефона
        if provider == "telegram_personal" and name.startswith("@"):
            username = name
        
        db_client = Client(
            pact_conversation_id=conversation_data.get("id"),  # В реальных вебхуках это 'id'
            pact_contact_id=None,  # Contact ID приходит только в message вебхуках
            pact_company_id=conversation_data.get("company_id", settings.pact_company_id),
            sender_external_id=conversation_data.get("sender_external_id"),
            sender_external_public_id=conversation_data.get("sender_external_public_id", conversation_data.get("sender_external_id")),
            name=name,
            phone_number=phone_number,
            username=username,
            avatar_url=conversation_data.get("avatar_url"),
            provider=provider,
            operational_state=conversation_data.get("operational_state", "open"),
            replied_state=conversation_data.get("replied_state", "initialized"),
            created_at=datetime.utcnow()
        )
        
        logger.info(f"Создаем клиента: {db_client.name}, провайдер: {db_client.provider}")
        
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        
        logger.info(f"Клиент успешно создан с ID: {db_client.id}")
        return db_client

    @staticmethod
    def update_client_from_pact(db: Session, client: Client, conversation_data: Dict) -> Client:
        """Обновить клиента из данных беседы Pact"""
        # Обновляем поля клиента из прямой структуры Pact webhook
        client.name = conversation_data.get("name", client.name)
        client.avatar_url = conversation_data.get("avatar_url", client.avatar_url)
        
        db.commit()
        db.refresh(client)
        return client

    @staticmethod
    def create_client(db: Session, client: ClientCreate) -> Client:
        """Создать клиента (для совместимости со схемами)"""
        db_client = Client(**client.model_dump())
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client

    @staticmethod
    def update_client(db: Session, client_id: int, client_update: ClientUpdate) -> Optional[Client]:
        """Обновить клиента"""
        db_client = db.query(Client).filter(Client.id == client_id).first()
        if db_client:
            update_data = client_update.model_dump(exclude_unset=True)
            
            # Если изменяется имя и не указан статус одобрения, сбрасываем одобрение
            if 'name' in update_data and 'name_approved' not in update_data:
                update_data['name_approved'] = False
            
            for field, value in update_data.items():
                setattr(db_client, field, value)
            db.commit()
            db.refresh(db_client)
        return db_client

    @staticmethod
    def update_last_message_info(db: Session, client_id: int, pact_message_id: int = None):
        """Обновить информацию о последнем сообщении"""
        client = db.query(Client).filter(Client.id == client_id).first()
        if client:
            client.last_message_at = datetime.utcnow()
            if pact_message_id:
                client.last_pact_message_id = pact_message_id
            db.commit()
            db.refresh(client)
        return client