from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from ..models.car_interest import CarInterest
from ..schemas.car_interest import CarInterestCreate, CarInterestUpdate
import logging
import json

logger = logging.getLogger(__name__)


class CarInterestService:
    @staticmethod
    def get_car_interest(db: Session, car_interest_id: int) -> Optional[CarInterest]:
        return db.query(CarInterest).filter(CarInterest.id == car_interest_id).first()

    @staticmethod
    def get_car_interest_by_client(db: Session, client_id: int) -> Optional[CarInterest]:
        return db.query(CarInterest).filter(CarInterest.client_id == client_id).first()

    @staticmethod
    def create_car_interest(db: Session, car_interest: CarInterestCreate) -> CarInterest:
        db_car_interest = CarInterest(**car_interest.model_dump())
        db.add(db_car_interest)
        db.commit()
        db.refresh(db_car_interest)
        return db_car_interest

    @staticmethod
    def update_car_interest(db: Session, car_interest_id: int, car_interest_update: CarInterestUpdate) -> Optional[CarInterest]:
        db_car_interest = db.query(CarInterest).filter(CarInterest.id == car_interest_id).first()
        if db_car_interest:
            update_data = car_interest_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_car_interest, field, value)
                # Flag JSON fields as modified so SQLAlchemy detects the change
                if field == 'structured_data':
                    flag_modified(db_car_interest, 'structured_data')
            db.commit()
            db.refresh(db_car_interest)
        return db_car_interest

    @staticmethod
    def update_or_create_car_interest(db: Session, client_id: int, structured_data: Dict[str, Any], notify_callback=None) -> CarInterest:
        """Обновить существующий car_interest или создать новый"""
        car_interest = CarInterestService.get_car_interest_by_client(db, client_id)
        if car_interest:
            car_interest_update = CarInterestUpdate(structured_data=structured_data)
            updated_car_interest = CarInterestService.update_car_interest(db, car_interest.id, car_interest_update)
        else:
            car_interest_create = CarInterestCreate(client_id=client_id, structured_data=structured_data)
            updated_car_interest = CarInterestService.create_car_interest(db, car_interest_create)
        
        # Вызываем callback для уведомления если он передан
        if notify_callback and updated_car_interest:
            try:
                car_interest_data = {
                    "id": updated_car_interest.id,
                    "client_id": updated_car_interest.client_id,
                    "structured_data": updated_car_interest.structured_data,
                    "last_updated": updated_car_interest.last_updated.isoformat() if updated_car_interest.last_updated else None
                }
                notify_callback(client_id, car_interest_data)
            except Exception as e:
                logger.error(f"Ошибка вызова callback уведомления: {e}")
        
        return updated_car_interest 