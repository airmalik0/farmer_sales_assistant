from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from ..models.client import Client
from ..schemas.client import ClientCreate, ClientUpdate


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
    def get_client_by_telegram_id(db: Session, telegram_id: int) -> Optional[Client]:
        return db.query(Client).options(
            joinedload(Client.messages),
            joinedload(Client.dossier),
            joinedload(Client.car_interest),
            joinedload(Client.tasks)
        ).filter(Client.telegram_id == telegram_id).first()

    @staticmethod
    def get_clients(db: Session, skip: int = 0, limit: int = 100) -> List[Client]:
        return db.query(Client).options(
            joinedload(Client.messages),
            joinedload(Client.dossier),
            joinedload(Client.car_interest),
            joinedload(Client.tasks)
        ).offset(skip).limit(limit).all()

    @staticmethod
    def create_client(db: Session, client: ClientCreate) -> Client:
        db_client = Client(**client.model_dump())
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client

    @staticmethod
    def update_client(db: Session, client_id: int, client_update: ClientUpdate) -> Optional[Client]:
        db_client = db.query(Client).filter(Client.id == client_id).first()
        if db_client:
            update_data = client_update.model_dump(exclude_unset=True)
            
            # Если изменяется имя и не указан статус одобрения, сбрасываем одобрение
            if ('first_name' in update_data or 'last_name' in update_data) and 'name_approved' not in update_data:
                update_data['name_approved'] = False
            
            for field, value in update_data.items():
                setattr(db_client, field, value)
            db.commit()
            db.refresh(db_client)
        return db_client

    @staticmethod
    def get_or_create_client(db: Session, telegram_id: int, first_name: str = None, 
                           last_name: str = None, username: str = None) -> Client:
        client = ClientService.get_client_by_telegram_id(db, telegram_id)
        if not client:
            client_data = ClientCreate(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username
            )
            client = ClientService.create_client(db, client_data)
        return client