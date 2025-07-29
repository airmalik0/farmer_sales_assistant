from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.task import Task
from ..models.client import Client
from ..schemas.task import TaskCreate, TaskUpdate
import logging
import asyncio

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
            asyncio.create_task(TaskService._send_task_notification(db, db_task))
        
        return db_task
    
    @staticmethod
    async def _send_task_notification(db: Session, task: Task):
        """Отправляет уведомление о новой задаче"""
        try:
            from ..services.telegram_service import TelegramService
            from ..services.client_service import ClientService
            
            # Получаем информацию о клиенте
            client = ClientService.get_client(db, task.client_id)
            if not client:
                logger.error(f"Клиент не найден для задачи {task.id}")
                return
            
            # Отправляем уведомление
            success = await TelegramService.send_task_notification_to_farmer(task, client)
            
            if success:
                # Отмечаем, что уведомление отправлено
                task.telegram_notification_sent = True
                db.commit()
                logger.info(f"Уведомление о задаче {task.id} успешно отправлено")
            else:
                logger.error(f"Не удалось отправить уведомление о задаче {task.id}")
                
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления о задаче {task.id}: {e}")

    @staticmethod
    def create_multiple_tasks(db: Session, client_id: int, tasks_data: List[dict], notify_callback=None) -> List[Task]:
        """Создать несколько задач для клиента из AI анализа"""
        created_tasks = []
        
        for task_data in tasks_data:
            task_create = TaskCreate(
                client_id=client_id,
                description=task_data.get('description', ''),
                due_date=task_data.get('due_date'),
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
    async def send_overdue_reminders(db: Session) -> int:
        """Отправляет напоминания о просроченных задачах"""
        from datetime import date
        from ..services.telegram_service import TelegramService
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
                    success = await TelegramService.send_task_reminder_to_farmer(task, client)
                    if success:
                        sent_count += 1
                        
            except Exception as e:
                logger.error(f"Ошибка отправки напоминания о задаче {task.id}: {e}")
        
        logger.info(f"Отправлено {sent_count} напоминаний о просроченных задачах")
        return sent_count 