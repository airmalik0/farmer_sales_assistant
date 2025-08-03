from datetime import datetime, date
from typing import Optional, List, Callable
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import or_, and_
import logging

from ..models.task import Task
from ..models.client import Client
from ..schemas.task import TaskCreate, TaskUpdate, TaskManualUpdate

logger = logging.getLogger(__name__)


class TaskService:
    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_tasks_by_client(db: Session, client_id: int) -> List[Task]:
        return db.query(Task).filter(Task.client_id == client_id).order_by(Task.created_at.desc()).all()

    @staticmethod
    def get_tasks_by_client_active(db: Session, client_id: int) -> List[Task]:
        """Получить только активные (не завершенные) задачи клиента"""
        return db.query(Task).filter(
            Task.client_id == client_id,
            Task.is_completed == False
        ).order_by(Task.due_date.asc(), Task.created_at.desc()).all()

    @staticmethod
    def create_task(db: Session, task: TaskCreate, send_notification: bool = True) -> Task:
        db_task = Task(**task.model_dump())
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # Отправляем уведомление фермеру (если это новая задача)
        if send_notification and not db_task.telegram_notification_sent:
            try:
                from .ai.notifications import sync_send_task_notification
                # Формируем данные задачи
                task_data = {
                    "id": db_task.id,
                    "client_id": db_task.client_id,
                    "description": db_task.description,
                    "due_date": db_task.due_date.isoformat() if db_task.due_date else None,
                    "is_completed": db_task.is_completed,
                    "priority": db_task.priority,
                    "source": db_task.source,
                    "created_at": db_task.created_at.isoformat() if db_task.created_at else None,
                    "updated_at": db_task.updated_at.isoformat() if db_task.updated_at else None
                }
                sync_send_task_notification(db_task.client_id, task_data)
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления о задаче: {e}")
        
        return db_task

    @staticmethod
    def _parse_due_date(due_date_str: str) -> Optional[datetime]:
        """Преобразует строку datetime в объект datetime с временем по умолчанию 8:00"""
        if not due_date_str:
            return None
            
        try:
            # Пытаемся парсить как datetime
            if 'T' in due_date_str:
                # ISO формат с T
                parsed_datetime = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                return parsed_datetime
            elif ' ' in due_date_str:
                # Формат 'YYYY-MM-DD HH:MM:SS' - время уже указано
                parsed_datetime = datetime.strptime(due_date_str, '%Y-%m-%d %H:%M:%S')
                return parsed_datetime
            else:
                # Только дата 'YYYY-MM-DD' - ставим время 8:00 утра
                parsed_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                return parsed_date.replace(hour=8, minute=0, second=0)
                
        except ValueError as e:
            logger.warning(f"Не удалось распарсить дату '{due_date_str}': {e}")
            return None

    @staticmethod
    def create_multiple_tasks(db: Session, client_id: int, tasks_data: List[dict], notify_callback=None) -> List[Task]:
        """Создать несколько задач для клиента из AI анализа"""
        created_tasks = []
        
        for task_data in tasks_data:
            # Преобразуем due_date из строки в date объект
            due_date_str = task_data.get('due_date')
            due_date = TaskService._parse_due_date(due_date_str) if due_date_str else None
            
            task_create = TaskCreate(
                client_id=client_id,
                description=task_data.get('description', ''),
                due_date=due_date,
                priority=task_data.get('priority', 'normal')
            )
            db_task = TaskService.create_task(db, task_create, send_notification=True)
            created_tasks.append(db_task)
        
        # Вызываем callback для уведомления если он передан
        if notify_callback and created_tasks:
            try:
                tasks_data = [{
                    "id": task.id,
                    "client_id": task.client_id,
                    "description": task.description,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "is_completed": task.is_completed,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                } for task in created_tasks]
                notify_callback(client_id, {"tasks": tasks_data})
            except Exception as e:
                logger.error(f"Ошибка вызова callback уведомления: {e}")
        
        return created_tasks

    @staticmethod
    def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if db_task:
            update_data = task_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_task, field, value)
            db.commit()
            db.refresh(db_task)
        return db_task

    @staticmethod
    def update_task_manually(db: Session, task_id: int, manual_update: TaskManualUpdate) -> Optional[Task]:
        """Обновить задачу вручную с отметкой о ручном изменении"""
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            return None
        
        # Получаем текущие extra_data
        current_extra_data = db_task.extra_data or {}
        manual_modifications = current_extra_data.get("manual_modifications", {})
        
        # Обновляем только те поля, которые переданы и действительно изменились
        update_data = manual_update.model_dump(exclude_unset=True)
        current_time = datetime.utcnow().isoformat()
        
        has_changes = False
        for field, new_value in update_data.items():
            if new_value is not None:  # Обновляем только если значение передано
                current_value = getattr(db_task, field, None)
                
                # Нормализуем значения для сравнения
                if field == "due_date":
                    # Для дат сравниваем строковые представления
                    normalized_current = current_value.isoformat() if current_value else None
                    normalized_new = new_value.isoformat() if hasattr(new_value, 'isoformat') else str(new_value) if new_value else None
                else:
                    normalized_current = current_value if current_value is not None else ""
                    normalized_new = new_value if new_value is not None else ""
                
                # Если значение действительно изменилось
                if normalized_current != normalized_new:
                    setattr(db_task, field, new_value)
                    manual_modifications[field] = {
                        "modified_at": current_time,
                        "modified_by": "human"
                    }
                    has_changes = True
        
        # Обновляем extra_data только если были изменения
        if has_changes:
            current_extra_data["manual_modifications"] = manual_modifications
            db_task.extra_data = current_extra_data
            flag_modified(db_task, 'extra_data')
            db.commit()
            db.refresh(db_task)
        
        return db_task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if db_task:
            db.delete(db_task)
            db.commit()
            return True
        return False

    @staticmethod
    def mark_task_completed(db: Session, task_id: int) -> Optional[Task]:
        """Отметить задачу как выполненную"""
        return TaskService.update_task(db, task_id, TaskUpdate(is_completed=True))

    @staticmethod
    def mark_task_pending(db: Session, task_id: int) -> Optional[Task]:
        """Отметить задачу как невыполненную"""
        return TaskService.update_task(db, task_id, TaskUpdate(is_completed=False))
    
    @staticmethod
    def complete_task(db: Session, task_id: int) -> Optional[Task]:
        """Отметить задачу как выполненную (алиас для mark_task_completed)"""
        return TaskService.mark_task_completed(db, task_id)
    
    @staticmethod
    async def send_overdue_reminders(db: Session) -> int:
        """Отправляет напоминания о просроченных задачах"""
        from datetime import date
        from ..services.telegram_admin_service import TelegramAdminService
        from ..services.client_service import ClientService
        
        # Получаем просроченные задачи
        today = date.today()
        overdue_tasks = db.query(Task).filter(
            Task.due_date < today,
            Task.is_completed == False
        ).all()
        
        sent_count = 0
        for task in overdue_tasks:
            try:
                client = ClientService.get_client(db, task.client_id)
                if client:
                    success = await TelegramAdminService.send_task_reminder_to_farmer(task, client)
                    if success:
                        sent_count += 1
                        
            except Exception as e:
                logger.error(f"Ошибка отправки напоминания о задаче {task.id}: {e}")
        
        logger.info(f"Отправлено {sent_count} напоминаний о просроченных задачах")
        return sent_count 