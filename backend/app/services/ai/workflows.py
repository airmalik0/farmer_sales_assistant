"""Рабочие процессы для анализа клиентов"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, date

from sqlalchemy.orm import Session
from sqlalchemy import text

from ...core.database import SessionLocal
from ...models.client import Client
from ...models.message import Message
from ...schemas.task import TaskUpdate
from ..message_service import MessageService
from ..dossier_service import DossierService
from ..car_interest_service import CarInterestService
from ..task_service import TaskService
from .dossier_agent import dossier_agent
from .car_interest_agent import car_interest_agent
from .task_agent import task_agent
from ..notification_service import (
    sync_send_dossier_notification,
    sync_send_car_interest_notification,
    sync_send_task_notification
)
from ..timer_service import analysis_timers

logger = logging.getLogger(__name__)


def _parse_due_date_for_update(due_date_str: str) -> datetime:
    """Преобразует строку datetime в объект datetime для обновлений задач с временем по умолчанию 8:00"""
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


class ClientAnalysisWorkflow:
    """Рабочий процесс для анализа клиента"""
    
    @staticmethod
    def format_chat_history(messages) -> str:
        """Форматирует историю чата для анализа AI"""
        formatted_messages = []
        for msg in messages:
            sender = "Клиент" if msg.sender.value == "client" else "Менеджер"
            content = msg.content
            
            # Добавляем информацию о типе контента
            if msg.content_type != "text":
                content = f"[{msg.content_type.upper()}] {content}"
            
            formatted_messages.append(f"{sender}: {content}")
        
        return "\n".join(formatted_messages)
    
    @staticmethod
    def analyze_client_complete(client_id: int) -> Dict[str, Any]:
        """Полный анализ клиента: досье, автомобильные интересы и задачи"""
        db = SessionLocal()
        try:
            logger.info(f"Начинаем полный анализ для клиента {client_id}")
            
            # Получаем клиента
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                error_msg = f"Клиент {client_id} не найден"
                logger.warning(error_msg)
                return {"error": error_msg}

            # Получаем историю чата
            messages = MessageService.get_chat_history(db, client_id)
            if not messages:
                info_msg = f"Нет сообщений для клиента {client_id}"
                logger.info(info_msg)
                return {"info": info_msg}

            client_name = client.first_name or f"ID {client.telegram_id}"
            results = {}
            
            # Анализ досье
            try:
                dossier_result = dossier_agent.analyze(client_id, client_name, messages)
                
                if dossier_result["updates"]:
                    # Обновляем только измененные поля
                    dossier = DossierService.update_or_create_dossier(
                        db, client_id, {"client_info": dossier_result["updates"]}, 
                        notify_callback=sync_send_dossier_notification
                    )
                    results["dossier"] = f"Досье для клиента {client_name} обновлено: {', '.join(dossier_result['updates'].keys())}"
                    logger.info(results["dossier"])
                elif dossier_result["confirmed"]:
                    results["dossier"] = f"Досье для клиента {client_name} подтверждено без изменений"
                    logger.info(results["dossier"])
                
                if dossier_result["errors"]:
                    results["dossier_errors"] = dossier_result["errors"]
                    
            except Exception as e:
                error_msg = f"Ошибка анализа досье: {str(e)}"
                logger.error(error_msg)
                results["dossier_error"] = error_msg
            
            # Анализ автомобильных интересов
            try:
                car_interest_result = car_interest_agent.analyze(client_id, client_name, messages)
                
                if car_interest_result["updates"]:
                    updates = car_interest_result["updates"]
                    
                    # Получаем текущие запросы
                    current_car_interest = CarInterestService.get_car_interest_by_client(db, client_id)
                    current_queries = []
                    if current_car_interest and current_car_interest.structured_data:
                        current_queries = current_car_interest.structured_data.get("queries", [])
                    
                    # Применяем удаления (в обратном порядке чтобы не сбить индексы)
                    for index in sorted(updates.get("delete_indices", []), reverse=True):
                        if 0 <= index < len(current_queries):
                            current_queries.pop(index)
                    
                    # Применяем обновления
                    for update in updates.get("update_queries", []):
                        index = update["index"]
                        if 0 <= index < len(current_queries):
                            current_queries[index] = update["query"]
                    
                    # Добавляем новые запросы
                    current_queries.extend(updates.get("add_queries", []))
                    
                    # Сохраняем обновленные запросы
                    car_interest = CarInterestService.update_or_create_car_interest(
                        db, client_id, {"queries": current_queries}, 
                        notify_callback=sync_send_car_interest_notification
                    )
                    
                    changes = []
                    if updates.get("add_queries"):
                        changes.append(f"добавлено {len(updates['add_queries'])}")
                    if updates.get("update_queries"):
                        changes.append(f"обновлено {len(updates['update_queries'])}")
                    if updates.get("delete_indices"):
                        changes.append(f"удалено {len(updates['delete_indices'])}")
                    
                    if changes:
                        results["car_interests"] = f"Автомобильные интересы для клиента {client_name}: {', '.join(changes)}"
                    
                    logger.info(results.get("car_interests", "Автомобильные интересы обновлены"))
                    
                elif car_interest_result["confirmed"]:
                    results["car_interests"] = f"Автомобильные интересы для клиента {client_name} подтверждены без изменений"
                    logger.info(results["car_interests"])
                
                if car_interest_result["errors"]:
                    results["car_interests_errors"] = car_interest_result["errors"]
                    
            except Exception as e:
                error_msg = f"Ошибка анализа автомобильных интересов: {str(e)}"
                logger.error(error_msg)
                results["car_interests_error"] = error_msg
            
            # Анализ задач
            try:
                task_result = task_agent.analyze(client_id, client_name, messages)
                
                # Создаем новые задачи
                if task_result["new_tasks"]:
                    created_tasks = TaskService.create_multiple_tasks(
                        db, client_id, task_result["new_tasks"], 
                        notify_callback=sync_send_task_notification
                    )
                    results["new_tasks"] = f"Создано {len(created_tasks)} новых задач для клиента {client_name}"
                    logger.info(results["new_tasks"])
                
                # Обновляем существующие задачи
                if task_result["updated_tasks"]:
                    for update in task_result["updated_tasks"]:
                        task_id = update.pop("task_id")
                        
                        # Преобразуем due_date если он есть
                        if "due_date" in update and update["due_date"]:
                            update["due_date"] = _parse_due_date_for_update(update["due_date"])
                        
                        # Создаем объект TaskUpdate из оставшихся полей
                        task_update = TaskUpdate(**update)
                        updated_task = TaskService.update_task(db, task_id, task_update)
                        
                        # Отправляем WebSocket уведомление
                        if updated_task:
                            sync_send_task_notification(
                                client_id,
                                {
                                    "id": updated_task.id,
                                    "client_id": updated_task.client_id,
                                    "description": updated_task.description,
                                    "due_date": updated_task.due_date.isoformat() if updated_task.due_date else None,
                                    "is_completed": updated_task.is_completed,
                                    "priority": updated_task.priority,
                                    "source": updated_task.source,
                                    "created_at": updated_task.created_at.isoformat() if updated_task.created_at else None,
                                    "updated_at": updated_task.updated_at.isoformat() if updated_task.updated_at else None
                                }
                            )
                    results["updated_tasks"] = f"Обновлено {len(task_result['updated_tasks'])} задач для клиента {client_name}"
                    logger.info(results["updated_tasks"])
                
                # Отмечаем выполненные задачи
                if task_result["completed_task_ids"]:
                    for task_id in task_result["completed_task_ids"]:
                        completed_task = TaskService.complete_task(db, task_id)
                        
                        # Отправляем WebSocket уведомление
                        if completed_task:
                            sync_send_task_notification(
                                client_id,
                                {
                                    "id": completed_task.id,
                                    "client_id": completed_task.client_id,
                                    "description": completed_task.description,
                                    "due_date": completed_task.due_date.isoformat() if completed_task.due_date else None,
                                    "is_completed": completed_task.is_completed,
                                    "priority": completed_task.priority,
                                    "source": completed_task.source,
                                    "created_at": completed_task.created_at.isoformat() if completed_task.created_at else None,
                                    "updated_at": completed_task.updated_at.isoformat() if completed_task.updated_at else None
                                }
                            )
                    results["completed_tasks"] = f"Выполнено {len(task_result['completed_task_ids'])} задач для клиента {client_name}"
                    logger.info(results["completed_tasks"])
                
                # Удаляем неактуальные задачи
                if task_result["deleted_task_ids"]:
                    for task_id in task_result["deleted_task_ids"]:
                        deleted = TaskService.delete_task(db, task_id)
                        
                        # Отправляем WebSocket уведомление об удалении
                        if deleted:
                            sync_send_task_notification(
                                client_id,
                                {
                                    "deleted_task_id": task_id
                                }
                            )
                    results["deleted_tasks"] = f"Удалено {len(task_result['deleted_task_ids'])} задач для клиента {client_name}"
                    logger.info(results["deleted_tasks"])
                
                if task_result["confirmed"] and not any([
                    task_result["new_tasks"],
                    task_result["updated_tasks"],
                    task_result["completed_task_ids"],
                    task_result["deleted_task_ids"]
                ]):
                    results["tasks"] = f"Задачи для клиента {client_name} подтверждены без изменений"
                    logger.info(results["tasks"])
                
                if task_result["errors"]:
                    results["tasks_errors"] = task_result["errors"]
                    
            except Exception as e:
                error_msg = f"Ошибка анализа задач: {str(e)}"
                logger.error(error_msg)
                results["tasks_error"] = error_msg
            
            return results
        
        except Exception as e:
            error_msg = f"Ошибка при полном анализе клиента {client_id}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
        finally:
            db.close()
    
    @staticmethod
    def analyze_client_dossier(client_id: int) -> str:
        """Анализ только досье клиента"""
        db = SessionLocal()
        try:
            logger.info(f"Начинаем анализ досье для клиента {client_id}")
            
            # Получаем клиента
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.warning(f"Клиент {client_id} не найден")
                return f"Клиент {client_id} не найден"

            # Получаем историю чата
            messages = MessageService.get_chat_history(db, client_id)
            if not messages:
                logger.info(f"Нет сообщений для клиента {client_id}")
                return f"Нет сообщений для клиента {client_id}"

            client_name = client.first_name or f"ID {client.telegram_id}"

            # Запускаем анализ досье
            dossier_result = dossier_agent.analyze(client_id, client_name, messages)
            
            if dossier_result["updates"]:
                # Обновляем только измененные поля
                dossier = DossierService.update_or_create_dossier(
                    db, client_id, {"client_info": dossier_result["updates"]}, 
                    notify_callback=sync_send_dossier_notification
                )
                result = f"Досье для клиента {client_name} обновлено: {', '.join(dossier_result['updates'].keys())}"
                logger.info(result)
                return result
            elif dossier_result["confirmed"]:
                result = f"Досье для клиента {client_name} подтверждено без изменений"
                logger.info(result)
                return result
            else:
                return f"Не удалось проанализировать досье для клиента {client_name}"
        
        except Exception as e:
            error_msg = f"Ошибка при анализе досье клиента {client_id}: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()
    
    @staticmethod
    def analyze_client_car_interests(client_id: int) -> str:
        """Анализ только автомобильных интересов клиента"""
        db = SessionLocal()
        try:
            logger.info(f"Начинаем анализ автомобильных интересов для клиента {client_id}")
            
            # Получаем клиента
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.warning(f"Клиент {client_id} не найден")
                return f"Клиент {client_id} не найден"

            # Получаем историю чата
            messages = MessageService.get_chat_history(db, client_id)
            if not messages:
                logger.info(f"Нет сообщений для клиента {client_id}")
                return f"Нет сообщений для клиента {client_id}"

            client_name = client.first_name or f"ID {client.telegram_id}"

            # Запускаем анализ автомобильных интересов
            car_interest_result = car_interest_agent.analyze(client_id, client_name, messages)
            
            if car_interest_result["updates"]:
                updates = car_interest_result["updates"]
                
                # Получаем текущие запросы
                current_car_interest = CarInterestService.get_car_interest_by_client(db, client_id)
                current_queries = []
                if current_car_interest and current_car_interest.structured_data:
                    current_queries = current_car_interest.structured_data.get("queries", [])
                
                # Применяем удаления (в обратном порядке)
                for index in sorted(updates.get("delete_indices", []), reverse=True):
                    if 0 <= index < len(current_queries):
                        current_queries.pop(index)
                
                # Применяем обновления
                for update in updates.get("update_queries", []):
                    index = update["index"]
                    if 0 <= index < len(current_queries):
                        current_queries[index] = update["query"]
                
                # Добавляем новые запросы
                current_queries.extend(updates.get("add_queries", []))
                
                # Сохраняем обновленные запросы
                car_interest = CarInterestService.update_or_create_car_interest(
                    db, client_id, {"queries": current_queries}, 
                    notify_callback=sync_send_car_interest_notification
                )
                
                changes = []
                if updates.get("add_queries"):
                    changes.append(f"добавлено {len(updates['add_queries'])}")
                if updates.get("update_queries"):
                    changes.append(f"обновлено {len(updates['update_queries'])}")
                if updates.get("delete_indices"):
                    changes.append(f"удалено {len(updates['delete_indices'])}")
                
                result = f"Автомобильные интересы для клиента {client_name}: {', '.join(changes)}"
                
                logger.info(result)
                return result
                
            elif car_interest_result["confirmed"]:
                result = f"Автомобильные интересы для клиента {client_name} подтверждены без изменений"
                logger.info(result)
                return result
            else:
                return f"Не удалось проанализировать автомобильные интересы для клиента {client_name}"
        
        except Exception as e:
            error_msg = f"Ошибка при анализе автомобильных интересов клиента {client_id}: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()
    
    @staticmethod
    def analyze_client_tasks(client_id: int) -> str:
        """Анализ только задач клиента"""
        db = SessionLocal()
        try:
            logger.info(f"Начинаем анализ задач для клиента {client_id}")
            
            # Получаем клиента
            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                logger.warning(f"Клиент {client_id} не найден")
                return f"Клиент {client_id} не найден"

            # Получаем историю чата
            messages = MessageService.get_chat_history(db, client_id)
            if not messages:
                logger.info(f"Нет сообщений для клиента {client_id}")
                return f"Нет сообщений для клиента {client_id}"

            client_name = client.first_name or f"ID {client.telegram_id}"

            # Запускаем анализ задач
            task_result = task_agent.analyze(client_id, client_name, messages)
            
            results = []
            
            # Создаем новые задачи
            if task_result["new_tasks"]:
                created_tasks = TaskService.create_multiple_tasks(
                    db, client_id, task_result["new_tasks"], 
                    notify_callback=sync_send_task_notification
                )
                results.append(f"Создано {len(created_tasks)} новых задач")
                logger.info(f"Создано {len(created_tasks)} новых задач для клиента {client_name}")
            
            # Обновляем существующие задачи
            if task_result["updated_tasks"]:
                for update in task_result["updated_tasks"]:
                    task_id = update.pop("task_id")
                    
                    # Преобразуем due_date если он есть
                    if "due_date" in update and update["due_date"]:
                        update["due_date"] = _parse_due_date_for_update(update["due_date"])
                    
                    task_update = TaskUpdate(**update)
                    TaskService.update_task(db, task_id, task_update)
                results.append(f"Обновлено {len(task_result['updated_tasks'])} задач")
                logger.info(f"Обновлено {len(task_result['updated_tasks'])} задач для клиента {client_name}")
            
            # Отмечаем выполненные задачи
            if task_result["completed_task_ids"]:
                for task_id in task_result["completed_task_ids"]:
                    TaskService.complete_task(db, task_id)
                results.append(f"Выполнено {len(task_result['completed_task_ids'])} задач")
                logger.info(f"Выполнено {len(task_result['completed_task_ids'])} задач для клиента {client_name}")
            
            # Удаляем неактуальные задачи
            if task_result["deleted_task_ids"]:
                for task_id in task_result["deleted_task_ids"]:
                    TaskService.delete_task(db, task_id)
                results.append(f"Удалено {len(task_result['deleted_task_ids'])} задач")
                logger.info(f"Удалено {len(task_result['deleted_task_ids'])} задач для клиента {client_name}")
            
            if task_result["confirmed"] and not any([
                task_result["new_tasks"],
                task_result["updated_tasks"],
                task_result["completed_task_ids"],
                task_result["deleted_task_ids"]
            ]):
                result = f"Задачи для клиента {client_name} подтверждены без изменений"
                logger.info(result)
                return result
            elif results:
                return f"Задачи для клиента {client_name}: {', '.join(results)}"
            else:
                return f"Не удалось проанализировать задачи для клиента {client_name}"
        
        except Exception as e:
            error_msg = f"Ошибка при анализе задач клиента {client_id}: {str(e)}"
            logger.error(error_msg)
            return error_msg
        finally:
            db.close()
    
    @staticmethod
    def schedule_analysis_after_delay(client_id: int, delay_minutes: int = 5) -> None:
        """Запланировать анализ диалога, автомобильных интересов и задач через указанное время"""
        def perform_analysis():
            try:
                logger.info(f"Выполняется запланированный анализ для клиента {client_id}")
                ClientAnalysisWorkflow.analyze_client_complete(client_id)
            except Exception as e:
                logger.error(f"Ошибка при запланированном анализе клиента {client_id}: {e}")
        
        # Используем механизм таймеров
        delay_seconds = delay_minutes * 60
        analysis_timers.schedule(client_id, perform_analysis, delay_seconds) 