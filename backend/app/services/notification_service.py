"""Сервис для WebSocket уведомлений"""

import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки WebSocket уведомлений"""
    
    @staticmethod
    async def send_dossier_notification(client_id: int, dossier_data: Dict[str, Any]) -> None:
        """Отправка уведомления о досье из фонового процесса"""
        try:
            # Импортируем здесь чтобы избежать циклических импортов
            from ..api.websocket import notify_dossier_update
            
            await notify_dossier_update(client_id, dossier_data)
            logger.info(f"WebSocket уведомление о досье отправлено для клиента {client_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки WebSocket уведомления о досье: {e}")
            # Продолжаем работу даже если уведомление не отправилось

    @staticmethod
    async def send_car_interest_notification(client_id: int, car_interest_data: Dict[str, Any]) -> None:
        """Отправка уведомления о автомобильных интересах из фонового процесса"""
        try:
            # Импортируем здесь чтобы избежать циклических импортов
            from ..api.websocket import notify_car_interest_update
            
            await notify_car_interest_update(client_id, car_interest_data)
            logger.info(f"WebSocket уведомление о автомобильных интересах отправлено для клиента {client_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки WebSocket уведомления о автомобильных интересах: {e}")
            # Продолжаем работу даже если уведомление не отправилось

    @staticmethod
    async def send_task_notification(client_id: int, task_data: Dict[str, Any]) -> None:
        """Отправка уведомления о задачах из фонового процесса"""
        try:
            # Импортируем здесь чтобы избежать циклических импортов
            from ..api.websocket import notify_task_update
            
            await notify_task_update(client_id, task_data)
            logger.info(f"WebSocket уведомление о задачах отправлено для клиента {client_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки WebSocket уведомления о задачах: {e}")
            # Продолжаем работу даже если уведомление не отправилось

    @staticmethod
    def sync_send_dossier_notification(client_id: int, dossier_data: Dict[str, Any]) -> None:
        """Синхронная обертка для отправки уведомления о досье"""
        try:
            asyncio.run(NotificationService.send_dossier_notification(client_id, dossier_data))
        except Exception as e:
            logger.error(f"Ошибка синхронной отправки уведомления о досье: {e}")

    @staticmethod
    def sync_send_car_interest_notification(client_id: int, car_interest_data: Dict[str, Any]) -> None:
        """Синхронная обертка для отправки уведомления о автомобильных интересах"""
        try:
            asyncio.run(NotificationService.send_car_interest_notification(client_id, car_interest_data))
        except Exception as e:
            logger.error(f"Ошибка синхронной отправки уведомления о автомобильных интересах: {e}")

    @staticmethod
    def sync_send_task_notification(client_id: int, task_data: Dict[str, Any]) -> None:
        """Синхронная обертка для отправки уведомления о задачах"""
        try:
            asyncio.run(NotificationService.send_task_notification(client_id, task_data))
        except Exception as e:
            logger.error(f"Ошибка синхронной отправки уведомления о задачах: {e}")


# Глобальный экземпляр сервиса
notification_service = NotificationService()

# Экспорт функций для обратной совместимости
send_dossier_notification = NotificationService.send_dossier_notification
send_car_interest_notification = NotificationService.send_car_interest_notification  
send_task_notification = NotificationService.send_task_notification
sync_send_dossier_notification = NotificationService.sync_send_dossier_notification
sync_send_car_interest_notification = NotificationService.sync_send_car_interest_notification
sync_send_task_notification = NotificationService.sync_send_task_notification 