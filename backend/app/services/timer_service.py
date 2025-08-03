"""Сервис для управления таймерами"""

import threading
import logging
from threading import Timer
from typing import Callable, Dict, Any

logger = logging.getLogger(__name__)


class TimerService:
    """Общий сервис для управления таймерами"""
    
    def __init__(self):
        self._timers: Dict[str, Timer] = {}
        self._lock = threading.Lock()
    
    def schedule(self, timer_id: str, callback: Callable, delay_seconds: float) -> None:
        """Запланировать выполнение callback через delay_seconds, отменив предыдущий таймер если есть"""
        with self._lock:
            # Отменяем старый таймер если существует
            if timer_id in self._timers:
                old_timer = self._timers[timer_id]
                old_timer.cancel()
                logger.info(f"Отменен предыдущий таймер {timer_id}")
            
            # Создаем новый таймер
            timer = Timer(delay_seconds, callback)
            timer.daemon = True
            timer.start()
            self._timers[timer_id] = timer
            logger.info(f"Запланирован таймер {timer_id} через {delay_seconds/60:.1f} минут")
    
    def cancel(self, timer_id: str) -> None:
        """Отменить запланированный таймер"""
        with self._lock:
            if timer_id in self._timers:
                self._timers[timer_id].cancel()
                del self._timers[timer_id]
                logger.info(f"Отменен таймер {timer_id}")
    
    def is_scheduled(self, timer_id: str) -> bool:
        """Проверить, запланирован ли таймер"""
        with self._lock:
            return timer_id in self._timers and self._timers[timer_id].is_alive()
    
    def get_active_timers_count(self) -> int:
        """Получить количество активных таймеров"""
        with self._lock:
            return len([timer for timer in self._timers.values() if timer.is_alive()])


class ClientAnalysisTimers:
    """Управление таймерами анализа для каждого клиента"""
    
    def __init__(self):
        self._timer_service = TimerService()
    
    def schedule(self, client_id: int, callback: Callable, delay_seconds: float) -> None:
        """Запланировать анализ для клиента, отменив предыдущий таймер если есть"""
        timer_id = f"client_analysis_{client_id}"
        self._timer_service.schedule(timer_id, callback, delay_seconds)
    
    def cancel(self, client_id: int) -> None:
        """Отменить запланированный анализ для клиента"""
        timer_id = f"client_analysis_{client_id}"
        self._timer_service.cancel(timer_id)
    
    def is_scheduled(self, client_id: int) -> bool:
        """Проверить, запланирован ли анализ для клиента"""
        timer_id = f"client_analysis_{client_id}"
        return self._timer_service.is_scheduled(timer_id)
    
    def get_active_timers_count(self) -> int:
        """Получить количество активных таймеров"""
        return self._timer_service.get_active_timers_count()


# Глобальные экземпляры сервисов
timer_service = TimerService()
analysis_timers = ClientAnalysisTimers() 