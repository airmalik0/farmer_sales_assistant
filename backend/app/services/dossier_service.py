from typing import Optional
from sqlalchemy.orm import Session
from ..models.dossier import Dossier
from ..schemas.dossier import DossierCreate, DossierUpdate


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
            db.commit()
            db.refresh(db_dossier)
        return db_dossier

    @staticmethod
    def update_or_create_dossier(db: Session, client_id: int, summary: str) -> Dossier:
        """Обновить существующее досье или создать новое"""
        dossier = DossierService.get_dossier_by_client(db, client_id)
        if dossier:
            dossier_update = DossierUpdate(summary=summary)
            return DossierService.update_dossier(db, dossier.id, dossier_update)
        else:
            dossier_create = DossierCreate(client_id=client_id, summary=summary)
            return DossierService.create_dossier(db, dossier_create)