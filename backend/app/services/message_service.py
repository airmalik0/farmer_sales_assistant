from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models.message import Message
from ..schemas.message import MessageCreate, MessageUpdate


class MessageService:
    @staticmethod
    def get_message(db: Session, message_id: int) -> Optional[Message]:
        return db.query(Message).filter(Message.id == message_id).first()

    @staticmethod
    def get_messages_by_client(db: Session, client_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        return (db.query(Message)
                .filter(Message.client_id == client_id)
                .order_by(desc(Message.timestamp))
                .offset(skip)
                .limit(limit)
                .all())

    @staticmethod
    def get_recent_messages(db: Session, skip: int = 0, limit: int = 100) -> List[Message]:
        return (db.query(Message)
                .order_by(desc(Message.timestamp))
                .offset(skip)
                .limit(limit)
                .all())

    @staticmethod
    def create_message(db: Session, message: MessageCreate) -> Message:
        db_message = Message(**message.model_dump())
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def update_message(db: Session, message_id: int, message_update: MessageUpdate) -> Optional[Message]:
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
                .filter(Message.client_id == client_id)
                .order_by(Message.timestamp)
                .all())