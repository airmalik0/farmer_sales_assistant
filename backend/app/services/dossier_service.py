from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from ..models.dossier import Dossier
from ..schemas.dossier import DossierCreate, DossierUpdate
import logging
import json

logger = logging.getLogger(__name__)


class DossierService:
    @staticmethod
    def get_dossier(db: Session, dossier_id: int) -> Optional[Dossier]:
        return db.query(Dossier).filter(Dossier.id == dossier_id).first()

    @staticmethod
    def get_dossier_by_client(db: Session, client_id: int) -> Optional[Dossier]:
        return db.query(Dossier).filter(Dossier.client_id == client_id).first()

    @staticmethod
    def create_dossier(db: Session, dossier: DossierCreate) -> Dossier:
        db_dossier = Dossier(**dossier.model_dump())
        db.add(db_dossier)
        db.commit()
        db.refresh(db_dossier)
        return db_dossier

    @staticmethod
    def update_dossier(db: Session, dossier_id: int, dossier_update: DossierUpdate) -> Optional[Dossier]:
        db_dossier = db.query(Dossier).filter(Dossier.id == dossier_id).first()
        if db_dossier:
            update_data = dossier_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_dossier, field, value)
                # Flag JSON fields as modified so SQLAlchemy detects the change
                if field == 'structured_data':
                    flag_modified(db_dossier, 'structured_data')
            db.commit()
            db.refresh(db_dossier)
        return db_dossier

    @staticmethod
    def update_or_create_dossier(db: Session, client_id: int, structured_data: Dict[str, Any], notify_callback=None) -> Dossier:
        """Обновить существующее досье или создать новое"""
        dossier = DossierService.get_dossier_by_client(db, client_id)
        if dossier:
            dossier_update = DossierUpdate(structured_data=structured_data)
            updated_dossier = DossierService.update_dossier(db, dossier.id, dossier_update)
        else:
            dossier_create = DossierCreate(client_id=client_id, structured_data=structured_data)
            updated_dossier = DossierService.create_dossier(db, dossier_create)
        
        # Вызываем callback для уведомления если он передан
        if notify_callback and updated_dossier:
            try:
                dossier_data = {
                    "id": updated_dossier.id,
                    "client_id": updated_dossier.client_id,
                    "structured_data": updated_dossier.structured_data,
                    "last_updated": updated_dossier.last_updated.isoformat() if updated_dossier.last_updated else None
                }
                notify_callback(client_id, dossier_data)
            except Exception as e:
                logger.error(f"Ошибка вызова callback уведомления: {e}")
        
        return updated_dossier