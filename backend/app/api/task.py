from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..core.database import get_db
from ..schemas import task as task_schemas
from ..services.task_service import TaskService
from ..services.client_service import ClientService
from .websocket import notify_task_update
import asyncio

router = APIRouter()


@router.get("/client/{client_id}", response_model=List[task_schemas.Task])
def get_tasks_by_client(client_id: int, active_only: bool = False, db: Session = Depends(get_db)):
    """Получить задачи клиента"""
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    if active_only:
        tasks = TaskService.get_tasks_by_client_active(db, client_id=client_id)
    else:
        tasks = TaskService.get_tasks_by_client(db, client_id=client_id)
    
    return tasks


@router.get("/{task_id}", response_model=task_schemas.Task)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Получить задачу по ID"""
    task = TaskService.get_task(db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@router.post("/", response_model=task_schemas.Task)
async def create_task(task: task_schemas.TaskCreate, db: Session = Depends(get_db)):
    """Создать новую задачу"""
    # Проверяем, что клиент существует
    client = ClientService.get_client(db, task.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    created_task = TaskService.create_task(db=db, task=task)
    
    # Уведомляем фронтенд о создании задачи
    await notify_task_update(
        client_id=created_task.client_id,
        task_data={
            "id": created_task.id,
            "client_id": created_task.client_id,
            "description": created_task.description,
            "due_date": created_task.due_date.isoformat() if created_task.due_date else None,
            "is_completed": created_task.is_completed,
            "priority": created_task.priority,
            "created_at": created_task.created_at.isoformat() if created_task.created_at else None,
            "updated_at": created_task.updated_at.isoformat() if created_task.updated_at else None
        }
    )
    
    return created_task


@router.put("/{task_id}", response_model=task_schemas.Task)
async def update_task(
    task_id: int, 
    task_update: task_schemas.TaskUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить задачу"""
    task = TaskService.update_task(db, task_id=task_id, task_update=task_update)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Уведомляем фронтенд об обновлении задачи
    await notify_task_update(
        client_id=task.client_id,
        task_data={
            "id": task.id,
            "client_id": task.client_id,
            "description": task.description,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "is_completed": task.is_completed,
            "priority": task.priority,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None
        }
    )
    
    return task


@router.put("/{task_id}/manual", response_model=task_schemas.Task)
async def update_task_manually(
    task_id: int,
    manual_update: task_schemas.TaskManualUpdate,
    db: Session = Depends(get_db)
):
    """Ручное обновление задачи с отметкой о ручном изменении"""
    
    # Получаем существующую задачу
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Подготавливаем данные для обновления
    update_data = manual_update.model_dump(exclude_unset=True)
    current_time = datetime.utcnow().isoformat()
    
    # Создаем структуру данных о ручных изменениях для задачи
    # Поскольку Task не имеет structured_data поля, мы создадим новое поле в модели
    # Но пока что просто обновим задачу обычным способом
    task_update = task_schemas.TaskUpdate(**update_data)
    updated_task = TaskService.update_task(db, task_id, task_update)
    
    if updated_task:
        # Уведомляем фронтенд об обновлении
        await notify_task_update(
            client_id=updated_task.client_id,
            task_data={
                "id": updated_task.id,
                "client_id": updated_task.client_id,
                "description": updated_task.description,
                "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None,
                "is_completed": updated_task.is_completed,
                "priority": updated_task.priority,
                "created_at": updated_task.created_at.isoformat() if updated_task.created_at else None,
                "updated_at": updated_task.updated_at.isoformat() if updated_task.updated_at else None,
                "manually_modified": True,  # Указываем, что задача была изменена вручную
                "manual_modification_time": current_time
            }
        )
    
    return updated_task


@router.post("/{task_id}/complete", response_model=task_schemas.Task)
async def mark_task_completed(task_id: int, db: Session = Depends(get_db)):
    """Отметить задачу как выполненную"""
    task = TaskService.mark_task_completed(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Уведомляем фронтенд об обновлении задачи
    await notify_task_update(
        client_id=task.client_id,
        task_data={
            "id": task.id,
            "client_id": task.client_id,
            "description": task.description,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "is_completed": task.is_completed,
            "priority": task.priority,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None
        }
    )
    
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Удалить задачу"""
    task = TaskService.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    client_id = task.client_id
    deleted = TaskService.delete_task(db, task_id)
    
    if not deleted:
        raise HTTPException(status_code=400, detail="Не удалось удалить задачу")
    
    # Уведомляем фронтенд об удалении задачи
    await notify_task_update(
        client_id=client_id,
        task_data={
            "deleted_task_id": task_id
        }
    )
    
    return {"message": "Задача удалена"} 