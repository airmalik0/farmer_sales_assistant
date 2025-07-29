from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas.task import TaskWithTrigger, Task as TaskSchema
from ..schemas.trigger import TriggerCreate, TriggerConditions, NotifyActionConfig, CreateTaskActionConfig
from ..models.trigger import TriggerAction, TriggerStatus
from ..services.task_service import TaskService
from ..services.trigger_service import TriggerService
from ..services.client_service import ClientService
from pydantic import BaseModel
import asyncio

router = APIRouter()


class NotificationTriggerRequest(BaseModel):
    """Модель для создания триггера уведомлений"""
    trigger_name: str
    conditions: Dict[str, Any]
    message: str = "Найден подходящий автомобиль!"
    channels: List[str] = ["telegram"]
    check_interval: int = 5


@router.post("/create-with-trigger", response_model=Dict[str, Any])
async def create_task_with_trigger(
    task_trigger: TaskWithTrigger,
    db: Session = Depends(get_db)
):
    """Создать задачу с автоматическим триггером"""
    
    # Проверяем существование клиента
    client = ClientService.get_client(db, task_trigger.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    try:
        # Создаем триггер
        trigger_conditions = TriggerConditions(**task_trigger.trigger_conditions)
        
        # Настройки действия триггера - создание задачи
        action_config = CreateTaskActionConfig(
            title=f"Автоматическая задача: {task_trigger.trigger_name}",
            description=task_trigger.description,
            priority=task_trigger.priority
        )
        
        trigger_data = TriggerCreate(
            name=task_trigger.trigger_name,
            description=f"Автоматический триггер для задачи клиента {client.first_name} {client.last_name}",
            status=TriggerStatus.ACTIVE,
            conditions=trigger_conditions,
            action_type=TriggerAction.CREATE_TASK,
            action_config=action_config.model_dump(),
            check_interval_minutes=5  # Проверяем каждые 5 минут
        )
        
        trigger = TriggerService.create_trigger(db, trigger_data)
        
        return {
            "success": True,
            "message": "Триггер создан и будет автоматически создавать задачи при срабатывании",
            "data": {
                "trigger_id": trigger.id,
                "trigger_name": trigger.name,
                "client_id": task_trigger.client_id,
                "client_name": f"{client.first_name} {client.last_name}".strip()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка создания триггера: {str(e)}")


@router.post("/notify-trigger", response_model=Dict[str, Any])
async def create_notification_trigger(
    request: NotificationTriggerRequest,
    db: Session = Depends(get_db)
):
    """Создать триггер уведомления (без привязки к конкретной задаче)"""
    
    try:
        # Создаем условия триггера
        trigger_conditions = TriggerConditions(**request.conditions)
        
        # Настройки действия триггера - уведомление
        action_config = NotifyActionConfig(
            message=request.message,
            channels=request.channels
        )
        
        trigger_data = TriggerCreate(
            name=request.trigger_name,
            description="Триггер для автоматических уведомлений",
            status=TriggerStatus.ACTIVE,
            conditions=trigger_conditions,
            action_type=TriggerAction.NOTIFY,
            action_config=action_config.model_dump(),
            check_interval_minutes=request.check_interval
        )
        
        trigger = TriggerService.create_trigger(db, trigger_data)
        
        return {
            "success": True,
            "message": "Триггер уведомлений создан",
            "data": {
                "trigger_id": trigger.id,
                "trigger_name": trigger.name,
                "action_type": "notify",
                "channels": request.channels
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка создания триггера: {str(e)}")


@router.get("/client/{client_id}/triggers", response_model=List[Dict[str, Any]])
def get_client_triggers(client_id: int, db: Session = Depends(get_db)):
    """Получить все триггеры, связанные с задачами клиента"""
    
    # Проверяем существование клиента
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Получаем задачи клиента
    tasks = TaskService.get_tasks_by_client(db, client_id)
    
    # Собираем уникальные триггеры
    trigger_ids = set()
    for task in tasks:
        if task.trigger_id:
            trigger_ids.add(task.trigger_id)
    
    triggers = []
    for trigger_id in trigger_ids:
        trigger = TriggerService.get_trigger(db, trigger_id)
        if trigger:
            triggers.append({
                "id": trigger.id,
                "name": trigger.name,
                "description": trigger.description,
                "status": trigger.status.value,
                "action_type": trigger.action_type.value,
                "conditions": trigger.conditions,
                "last_triggered_at": trigger.last_triggered_at,
                "trigger_count": trigger.trigger_count
            })
    
    return triggers


@router.get("/client/{client_id}/tasks-with-triggers", response_model=List[Dict[str, Any]])
def get_client_tasks_with_triggers(client_id: int, db: Session = Depends(get_db)):
    """Получить задачи клиента с информацией о связанных триггерах"""
    
    # Проверяем существование клиента
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Получаем задачи клиента
    tasks = TaskService.get_tasks_by_client(db, client_id)
    
    result = []
    for task in tasks:
        task_data = {
            "id": task.id,
            "description": task.description,
            "due_date": task.due_date,
            "is_completed": task.is_completed,
            "priority": task.priority,
            "source": task.source,
            "telegram_notification_sent": task.telegram_notification_sent,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "trigger": None
        }
        
        # Добавляем информацию о триггере, если есть
        if task.trigger_id:
            trigger = TriggerService.get_trigger(db, task.trigger_id)
            if trigger:
                task_data["trigger"] = {
                    "id": trigger.id,
                    "name": trigger.name,
                    "status": trigger.status.value,
                    "conditions": trigger.conditions,
                    "last_triggered_at": trigger.last_triggered_at
                }
        
        result.append(task_data)
    
    return result


@router.post("/trigger/{trigger_id}/toggle-for-client/{client_id}")
def toggle_trigger_for_client(
    trigger_id: int,
    client_id: int,
    db: Session = Depends(get_db)
):
    """Включить/выключить триггер для конкретного клиента"""
    
    # Проверяем существование клиента и триггера
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    trigger = TriggerService.get_trigger(db, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Триггер не найден")
    
    # Переключаем статус триггера
    new_status = TriggerStatus.INACTIVE if trigger.status == TriggerStatus.ACTIVE else TriggerStatus.ACTIVE
    
    from ..schemas.trigger import TriggerUpdate
    update_data = TriggerUpdate(status=new_status)
    updated_trigger = TriggerService.update_trigger(db, trigger_id, update_data)
    
    return {
        "success": True,
        "message": f"Триггер {trigger.name} {'активирован' if new_status == TriggerStatus.ACTIVE else 'деактивирован'}",
        "data": {
            "trigger_id": trigger_id,
            "client_id": client_id,
            "new_status": new_status.value
        }
    }


@router.post("/send-daily-summary")
async def send_daily_tasks_summary(db: Session = Depends(get_db)):
    """Отправить ежедневную сводку задач фермеру"""
    try:
        from ..services.telegram_service import TelegramService
        
        success = await TelegramService.send_daily_tasks_summary(db)
        
        if success:
            return {
                "success": True,
                "message": "Ежедневная сводка отправлена"
            }
        else:
            raise HTTPException(status_code=500, detail="Не удалось отправить сводку")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отправки сводки: {str(e)}")


@router.post("/send-overdue-reminders")
async def send_overdue_reminders(db: Session = Depends(get_db)):
    """Отправить напоминания о просроченных задачах"""
    try:
        sent_count = await TaskService.send_overdue_reminders(db)
        
        return {
            "success": True,
            "message": f"Отправлено {sent_count} напоминаний о просроченных задачах",
            "sent_count": sent_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отправки напоминаний: {str(e)}") 