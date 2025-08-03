from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from ..models.trigger import Trigger, TriggerLog, TriggerStatus, TriggerAction
from ..schemas.trigger import TriggerCreate, TriggerUpdate, TriggerLogCreate
from .google_sheets_service import google_sheets_service, CarData
from datetime import datetime, timedelta, timezone
import logging
import json
import asyncio
import httpx

logger = logging.getLogger(__name__)

# Настройка более детального логирования для триггеров
trigger_logger = logging.getLogger("triggers")
trigger_logger.setLevel(logging.INFO)


class TriggerService:
    @staticmethod
    def get_trigger(db: Session, trigger_id: int) -> Optional[Trigger]:
        """Получить триггер по ID"""
        return db.query(Trigger).options(
            joinedload(Trigger.trigger_logs)
        ).filter(Trigger.id == trigger_id).first()

    @staticmethod
    def get_triggers(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[TriggerStatus] = None
    ) -> List[Trigger]:
        """Получить список триггеров"""
        query = db.query(Trigger).options(joinedload(Trigger.trigger_logs))
        
        if status:
            query = query.filter(Trigger.status == status)
            
        return query.order_by(desc(Trigger.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def create_trigger(db: Session, trigger_data: TriggerCreate) -> Trigger:
        """Создать новый триггер"""
        # Преобразуем conditions в JSON-сериализуемый формат
        conditions_dict = trigger_data.conditions.model_dump(exclude_unset=True)
        
        db_trigger = Trigger(
            name=trigger_data.name,
            description=trigger_data.description,
            status=trigger_data.status,
            conditions=conditions_dict,
            action_type=trigger_data.action_type,
            action_config=trigger_data.action_config,
            check_interval_minutes=trigger_data.check_interval_minutes
        )
        
        db.add(db_trigger)
        db.commit()
        db.refresh(db_trigger)
        return db_trigger

    @staticmethod
    def update_trigger(
        db: Session, 
        trigger_id: int, 
        trigger_update: TriggerUpdate
    ) -> Optional[Trigger]:
        """Обновить триггер"""
        db_trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
        if not db_trigger:
            return None
        
        update_data = trigger_update.model_dump(exclude_unset=True)
        
        # Специальная обработка для conditions
        if 'conditions' in update_data and update_data['conditions']:
            update_data['conditions'] = update_data['conditions'].model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_trigger, field, value)
        
        db.commit()
        db.refresh(db_trigger)
        return db_trigger

    @staticmethod
    def delete_trigger(db: Session, trigger_id: int) -> bool:
        """Удалить триггер"""
        db_trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
        if db_trigger:
            db.delete(db_trigger)
            db.commit()
            return True
        return False

    @staticmethod
    def check_trigger_condition(trigger: Trigger, car: CarData) -> bool:
        """Проверить, соответствует ли автомобиль условиям триггера"""
        conditions = trigger.conditions
        
        # Проверяем ID автомобиля
        if 'car_id' in conditions and conditions['car_id']:
            if car.car_id != conditions['car_id']:
                return False
        
        # Проверяем марку
        if 'brand' in conditions and conditions['brand']:
            brands = conditions['brand'] if isinstance(conditions['brand'], list) else [conditions['brand']]
            if car.brand not in brands:
                return False
        
        # Проверяем модель
        if 'model' in conditions and conditions['model']:
            models = conditions['model'] if isinstance(conditions['model'], list) else [conditions['model']]
            if car.model not in models:
                return False
        
        # Проверяем локацию
        if 'location' in conditions and conditions['location']:
            if car.location != conditions['location']:
                return False
        
        # Проверяем цену
        if 'price_min' in conditions and conditions['price_min'] is not None:
            if car.price is None or car.price < conditions['price_min']:
                return False
        
        if 'price_max' in conditions and conditions['price_max'] is not None:
            if car.price is None or car.price > conditions['price_max']:
                return False
        
        # Проверяем год
        if 'year_min' in conditions and conditions['year_min'] is not None:
            if car.year is None or car.year < conditions['year_min']:
                return False
        
        if 'year_max' in conditions and conditions['year_max'] is not None:
            if car.year is None or car.year > conditions['year_max']:
                return False
        
        # Проверяем пробег
        if 'mileage_max' in conditions and conditions['mileage_max'] is not None:
            if car.mileage is None or car.mileage > conditions['mileage_max']:
                return False
        
        # Проверяем статус
        if 'status' in conditions and conditions['status']:
            statuses = conditions['status'] if isinstance(conditions['status'], list) else [conditions['status']]
            if car.status not in statuses:
                return False
        
        return True

    @staticmethod
    async def execute_trigger_action(
        db: Session, 
        trigger: Trigger, 
        car_data: CarData
    ) -> Dict[str, Any]:
        """Выполнить действие триггера"""
        action_result = {
            "success": False,
            "message": "",
            "data": {}
        }
        
        try:
            if trigger.action_type == TriggerAction.NOTIFY:
                result = await TriggerService._execute_notify_action(trigger, car_data)
                action_result.update(result)
            
            elif trigger.action_type == TriggerAction.CREATE_TASK:
                result = await TriggerService._execute_create_task_action(db, trigger, car_data)
                action_result.update(result)
            
            elif trigger.action_type == TriggerAction.WEBHOOK:
                result = await TriggerService._execute_webhook_action(trigger, car_data)
                action_result.update(result)
            
            else:
                action_result["message"] = f"Неподдерживаемый тип действия: {trigger.action_type}"
        
        except Exception as e:
            logger.error(f"Ошибка выполнения действия триггера {trigger.id}: {e}")
            action_result["message"] = str(e)
        
        return action_result

    @staticmethod
    async def _execute_notify_action(trigger: Trigger, car_data: CarData) -> Dict[str, Any]:
        """Выполнить действие уведомления"""
        from ..services.telegram_admin_service import TelegramAdminService
        
        config = trigger.action_config or {}
        message = config.get('message', f'Триггер {trigger.name} сработал')
        channels = config.get('channels', ['telegram'])
        
        # Заменяем плейсхолдеры в сообщении
        formatted_message = TriggerService._format_message(message, car_data)
        
        notifications_sent = []
        success_count = 0
        
        for channel in channels:
            if channel == 'websocket':
                # Отправляем уведомления через WebSocket
                notifications_sent.append(f'websocket: {formatted_message}')
                success_count += 1
            elif channel == 'telegram':
                success = await TelegramAdminService.send_notification(
                    f"🎯 Сработал триггер: {trigger.name}\n"
                    f"Автомобиль: {car_data.car_id}\n"
                    f"Цена: {car_data.price}\n"
                    f"Локация: {car_data.location}\n"
                    f"Пробег: {car_data.mileage}\n"
                    f"Статус: {car_data.status}\n"
                    f"Триггер: {trigger.name}\n"
                    f"Сообщение: {formatted_message}"
                )
                notifications_sent.append(f'telegram: {"✅" if success else "❌"} {formatted_message}')
                if success:
                    success_count += 1
        
        return {
            "success": success_count > 0,
            "message": f"Отправлено {success_count} из {len(channels)} уведомлений",
            "data": {
                "notifications": notifications_sent,
                "formatted_message": formatted_message,
                "success_count": success_count
            }
        }

    @staticmethod
    async def _execute_create_task_action(
        db: Session, 
        trigger: Trigger, 
        car_data: CarData
    ) -> Dict[str, Any]:
        """Выполнить действие создания задачи"""
        from .task_service import TaskService
        from ..schemas.task import TaskCreate
        
        config = trigger.action_config or {}
        title = config.get('title', f'Задача от триггера {trigger.name}')
        description = config.get('description', f'Автомобиль {car_data.car_id} соответствует условиям триггера')
        priority = config.get('priority', 'medium')
        
        # Форматируем заголовок и описание
        formatted_title = TriggerService._format_message(title, car_data)
        formatted_description = TriggerService._format_message(description, car_data)
        
        # Создаем задачу (используем реальные поля модели Task)
        task_data = TaskCreate(
            client_id=1,  # Системная задача для админа
            description=f"{formatted_title}\n\n{formatted_description}\n\nТриггер: {trigger.name}",
            priority=priority,
            source="trigger",
            trigger_id=trigger.id,
            extra_data={
                "trigger_name": trigger.name,
                "car_data": car_data.to_dict()
            }
        )
        
        task = TaskService.create_task(db, task_data, send_notification=True)
        
        return {
            "success": True,
            "message": "Задача создана",
            "data": {
                "task_id": task.id,
                "title": formatted_title
            }
        }

    @staticmethod
    async def _execute_webhook_action(trigger: Trigger, car_data: CarData) -> Dict[str, Any]:
        """Выполнить webhook действие"""
        config = trigger.action_config or {}
        url = config.get('url')
        method = config.get('method', 'POST')
        headers = config.get('headers', {})
        
        if not url:
            return {
                "success": False,
                "message": "URL не указан в конфигурации webhook"
            }
        
        payload = {
            "trigger_id": trigger.id,
            "trigger_name": trigger.name,
            "car_data": car_data.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            return {
                "success": response.is_success,
                "message": f"Webhook вызван: {response.status_code}",
                "data": {
                    "status_code": response.status_code,
                    "response_text": response.text[:500]  # Ограничиваем размер
                }
            }

    @staticmethod
    def _format_message(message: str, car_data: CarData) -> str:
        """Форматирует сообщение, заменяя плейсхолдеры данными автомобиля"""
        replacements = {
            '{car_id}': car_data.car_id or 'N/A',
            '{brand}': car_data.brand or 'N/A',
            '{model}': car_data.model or 'N/A',
            '{price}': f'${car_data.price:,.0f}' if car_data.price else 'N/A',
            '{location}': car_data.location or 'N/A',
            '{year}': str(car_data.year) if car_data.year else 'N/A',
            '{status}': car_data.status or 'N/A',
            '{mileage}': f'{car_data.mileage:,} км' if car_data.mileage else 'N/A'
        }
        
        formatted_message = message
        for placeholder, value in replacements.items():
            formatted_message = formatted_message.replace(placeholder, value)
        
        return formatted_message

    @staticmethod
    async def check_all_triggers(db: Session) -> Dict[str, Any]:
        """Проверить все активные триггеры"""
        # Получаем активные триггеры, которые нужно проверить
        now = datetime.now(timezone.utc)
        triggers = db.query(Trigger).filter(
            Trigger.status == TriggerStatus.ACTIVE
        ).all()
        
        trigger_logger.info(f"Найдено {len(triggers)} активных триггеров")
        
        # Фильтруем триггеры по времени последней проверки
        triggers_to_check = []
        for trigger in triggers:
            if trigger.last_checked_at is None:
                triggers_to_check.append(trigger)
                trigger_logger.debug(f"Триггер {trigger.name} (ID: {trigger.id}) добавлен для проверки - никогда не проверялся")
            else:
                time_since_check = now - trigger.last_checked_at
                if time_since_check.total_seconds() >= trigger.check_interval_minutes * 60:
                    triggers_to_check.append(trigger)
                    trigger_logger.debug(f"Триггер {trigger.name} (ID: {trigger.id}) добавлен для проверки - прошло {time_since_check.total_seconds()} секунд")
        
        trigger_logger.info(f"К проверке готово {len(triggers_to_check)} триггеров")
        
        if not triggers_to_check:
            return {
                "triggers_checked": 0,
                "triggers_fired": 0,
                "message": "Нет триггеров для проверки"
            }
        
        # Получаем данные из Google Sheets с повторными попытками
        cars = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                cars = google_sheets_service.get_sheet_data()
                if cars:
                    break
                trigger_logger.warning(f"Попытка {attempt + 1}: Нет данных из Google Sheets")
            except Exception as e:
                trigger_logger.error(f"Попытка {attempt + 1}: Ошибка получения данных из Google Sheets: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # Экспоненциальная задержка
        
        if not cars:
            # Обновляем время проверки для всех триггеров, даже если данных нет
            for trigger in triggers_to_check:
                trigger.last_checked_at = now
            db.commit()
            
            trigger_logger.warning("Не удалось получить данные из Google Sheets после всех попыток")
            return {
                "triggers_checked": len(triggers_to_check),
                "triggers_fired": 0,
                "message": f"Обновлено время проверки для {len(triggers_to_check)} триггеров, но нет данных из Google Sheets",
                "error": "Google Sheets недоступен"
            }
        
        trigger_logger.info(f"Получено {len(cars)} автомобилей из Google Sheets")
        fired_triggers = []
        triggers_with_errors = []
        
        # Проверяем каждый триггер с изоляцией ошибок
        for trigger in triggers_to_check:
            try:
                trigger_logger.debug(f"Проверяем триггер {trigger.name} (ID: {trigger.id})")
                
                # Обновляем время последней проверки
                trigger.last_checked_at = now
                
                # Проверяем условия для каждого автомобиля
                trigger_fired = False
                for car in cars:
                    try:
                        if TriggerService.check_trigger_condition(trigger, car):
                            trigger_logger.info(f"Триггер {trigger.name} сработал для автомобиля {car.car_id}")
                            
                            fired_triggers.append({
                                "trigger": trigger,
                                "car": car
                            })
                            
                            # Обновляем статистику триггера
                            trigger.last_triggered_at = now
                            trigger.trigger_count += 1
                            trigger_fired = True
                            
                            # Логируем срабатывание
                            log_entry = TriggerLog(
                                trigger_id=trigger.id,
                                trigger_data=car.to_dict(),
                                success=True
                            )
                            db.add(log_entry)
                            
                            # Выполняем действие триггера
                            try:
                                action_result = await TriggerService.execute_trigger_action(db, trigger, car)
                                trigger_logger.info(f"Действие триггера выполнено: {action_result.get('message', 'OK')}")
                                
                                # Обновляем лог с результатом действия
                                log_entry.action_result = action_result
                                log_entry.success = action_result.get('success', False)
                                
                            except Exception as action_error:
                                trigger_logger.error(f"Ошибка выполнения действия триггера {trigger.name}: {action_error}")
                                log_entry.success = False
                                log_entry.error_message = str(action_error)
                    
                    except Exception as car_error:
                        trigger_logger.error(f"Ошибка проверки автомобиля {car.car_id} для триггера {trigger.name}: {car_error}")
                        # Продолжаем проверку других автомобилей
                        continue
                
                # Сохраняем изменения для этого триггера
                db.commit()
                
            except Exception as trigger_error:
                trigger_logger.error(f"Критическая ошибка при проверке триггера {trigger.name} (ID: {trigger.id}): {trigger_error}")
                triggers_with_errors.append({
                    "trigger_id": trigger.id,
                    "trigger_name": trigger.name,
                    "error": str(trigger_error)
                })
                
                # Обновляем время проверки даже при ошибке
                try:
                    trigger.last_checked_at = now
                    db.commit()
                except Exception as commit_error:
                    trigger_logger.error(f"Ошибка сохранения времени проверки для триггера {trigger.id}: {commit_error}")
                    db.rollback()
        
        # Финальная фиксация всех изменений
        try:
            db.commit()
        except Exception as final_commit_error:
            trigger_logger.error(f"Ошибка финального сохранения: {final_commit_error}")
            db.rollback()
        
        result = {
            "triggers_checked": len(triggers_to_check),
            "triggers_fired": len(fired_triggers),
            "triggers_with_errors": len(triggers_with_errors),
            "message": f"Проверено {len(triggers_to_check)} триггеров, сработало {len(fired_triggers)}, ошибок {len(triggers_with_errors)}",
            "fired_triggers": [
                {
                    "trigger_name": item["trigger"].name,
                    "car_id": item["car"].car_id
                }
                for item in fired_triggers
            ]
        }
        
        if triggers_with_errors:
            result["errors"] = triggers_with_errors
        
        trigger_logger.info(f"Результат проверки триггеров: {result['message']}")
        return result

    @staticmethod
    def get_trigger_logs(
        db: Session, 
        trigger_id: int = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TriggerLog]:
        """Получить логи срабатывания триггеров"""
        query = db.query(TriggerLog)
        
        if trigger_id:
            query = query.filter(TriggerLog.trigger_id == trigger_id)
        
        return query.order_by(desc(TriggerLog.triggered_at)).offset(skip).limit(limit).all()

    @staticmethod
    def get_trigger_stats(db: Session, trigger_id: int) -> Dict[str, Any]:
        """Получить статистику по триггеру"""
        trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
        if not trigger:
            return {}
        
        # Статистика за последние 30 дней
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_logs = db.query(TriggerLog).filter(
            TriggerLog.trigger_id == trigger_id,
            TriggerLog.triggered_at >= thirty_days_ago
        ).all()
        
        return {
            "total_triggers": trigger.trigger_count,
            "triggers_last_30_days": len(recent_logs),
            "last_triggered": trigger.last_triggered_at,
            "last_checked": trigger.last_checked_at,
            "status": trigger.status.value,
            "check_interval_minutes": trigger.check_interval_minutes
        } 