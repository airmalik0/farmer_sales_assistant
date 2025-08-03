from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime
from ..models.message import Message, MessageAttachment, SenderType
from ..schemas.message import MessageCreate, MessageUpdate


class MessageService:
    @staticmethod
    def get_message(db: Session, message_id: int) -> Optional[Message]:
        return db.query(Message).options(
            joinedload(Message.attachments)
        ).filter(Message.id == message_id).first()

    @staticmethod
    def get_messages_by_client(db: Session, client_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        return (db.query(Message)
                .options(joinedload(Message.attachments))
                .filter(Message.client_id == client_id)
                .order_by(desc(Message.timestamp))
                .offset(skip)
                .limit(limit)
                .all())

    @staticmethod
    def get_recent_messages(db: Session, skip: int = 0, limit: int = 100) -> List[Message]:
        return (db.query(Message)
                .options(joinedload(Message.attachments))
                .order_by(desc(Message.timestamp))
                .offset(skip)
                .limit(limit)
                .all())

    @staticmethod
    def create_message_from_pact(db: Session, client_id: int, message_data: Dict) -> Message:
        """Создать сообщение из данных Pact webhook"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Создание сообщения для клиента {client_id} из данных: {message_data}")
        
        # Определяем направление сообщения
        income = message_data.get("income", True)
        sender = SenderType.client if income else SenderType.farmer
        
        # Создаем сообщение
        db_message = Message(
            client_id=client_id,
            pact_message_id=message_data.get("id"),  # В реальных Pact вебхуках это просто 'id'
            external_id=message_data.get("external_id") or str(message_data.get("id")),
            external_created_at=_parse_datetime(message_data.get("external_created_at") or message_data.get("created_at")),
            sender=sender,
            content_type=_determine_content_type(message_data),
            content=message_data.get("message"),  # В Pact это поле называется "message"
            income=income,
            status=message_data.get("status", "created"),
            replied_to_id=message_data.get("replied_to_id"),
            reactions=message_data.get("reactions", []),
            details=message_data.get("details"),
            timestamp=datetime.utcnow()
        )
        
        db.add(db_message)
        db.flush()  # Получаем ID сообщения
        
        # Создаем attachments если есть
        attachments_data = message_data.get("attachments", [])
        for attachment_data in attachments_data:
            attachment = MessageAttachment(
                message_id=db_message.id,
                pact_attachment_id=attachment_data.get("id"),
                file_name=attachment_data.get("file_name", "unknown"),
                mime_type=attachment_data.get("mime_type", "application/octet-stream"),
                size=attachment_data.get("size", 0),
                attachment_url=attachment_data.get("attachment_url", ""),
                preview_url=attachment_data.get("preview_url"),
                aspect_ratio=attachment_data.get("aspect_ratio"),
                width=attachment_data.get("width"),
                height=attachment_data.get("height"),
                push_to_talk=attachment_data.get("push_to_talk", False)
            )
            db.add(attachment)
        
        db.commit()
        db.refresh(db_message)
        
        # Обновляем время последнего сообщения у клиента
        from .client_service import ClientService
        ClientService.update_last_message_info(
            db, client_id, db_message.pact_message_id
        )
        
        logger.info(f"Сообщение успешно создано с ID: {db_message.id}")
        return db_message

    @staticmethod
    def create_message(db: Session, message: MessageCreate) -> Message:
        """Создать сообщение (для совместимости со схемами)"""
        db_message = Message(**message.model_dump())
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def update_message_from_pact(db: Session, message: Message, message_data: Dict) -> Message:
        """Обновить сообщение из данных Pact"""
        message.status = message_data.get("status", message.status)
        message.details = message_data.get("details", message.details)
        message.reactions = message_data.get("reactions", message.reactions)
        
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def update_message(db: Session, message_id: int, message_update: MessageUpdate) -> Optional[Message]:
        """Обновить сообщение"""
        db_message = db.query(Message).filter(Message.id == message_id).first()
        if db_message:
            update_data = message_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_message, field, value)
            db.commit()
            db.refresh(db_message)
        return db_message

    @staticmethod
    def get_chat_history(db: Session, client_id: int) -> List[Message]:
        """Получить всю историю чата с клиентом для анализа AI"""
        return (db.query(Message)
                .options(joinedload(Message.attachments))
                .filter(Message.client_id == client_id)
                .order_by(Message.timestamp)
                .all())

    @staticmethod
    def find_message_by_pact_id(db: Session, pact_message_id: int) -> Optional[Message]:
        """Найти сообщение по Pact message ID"""
        return db.query(Message).filter(Message.pact_message_id == pact_message_id).first()

    @staticmethod
    def get_message_stats(db: Session, client_id: int = None) -> Dict:
        """Получить статистику сообщений"""
        query = db.query(Message)
        if client_id:
            query = query.filter(Message.client_id == client_id)
        
        total = query.count()
        incoming = query.filter(Message.income == True).count()
        outgoing = query.filter(Message.income == False).count()
        
        return {
            "total": total,
            "incoming": incoming,
            "outgoing": outgoing
        }


def _determine_content_type(message_data: Dict) -> str:
    """Определить тип контента сообщения"""
    if message_data.get("attachments"):
        return "attachment"
    return "text"


def _parse_datetime(datetime_str: str) -> Optional[datetime]:
    """Парсинг даты из строки"""
    if not datetime_str:
        return None
    
    try:
        # Попробуем разные форматы
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO с микросекундами
            "%Y-%m-%dT%H:%M:%SZ",     # ISO без микросекунд
            "%Y-%m-%d %H:%M:%S",      # Обычный формат
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        return None
    except Exception:
        return None