"""
AI сервис на основе LangGraph для анализа клиентских диалогов

Этот модуль предоставляет современный подход к анализу клиентов с использованием:
- LangGraph для управления состоянием агентов
- Structured output для надежного парсинга
- ReACT паттерн для tool-вызовов
"""

from .base_agent import BaseAnalysisAgent
from .dossier_agent import DossierAnalysisAgent, DossierAnalysisState, dossier_agent
from .car_interest_agent import CarInterestAnalysisAgent, CarInterestAnalysisState, car_interest_agent
from .task_agent import TaskAnalysisAgent, TaskAnalysisState, task_agent
from .workflows import ClientAnalysisWorkflow
from .schemas import DOSSIER_SCHEMA, TASK_SCHEMA, CAR_INTEREST_SCHEMA
from .tools import DOSSIER_TOOLS, CAR_INTEREST_TOOLS, TASK_TOOLS

# Импорты из общих сервисов
from ..notification_service import (
    send_dossier_notification,
    send_car_interest_notification,
    send_task_notification,
    sync_send_dossier_notification,
    sync_send_car_interest_notification,
    sync_send_task_notification
)
from ..timer_service import analysis_timers

__all__ = [
    # Базовый агент
    'BaseAnalysisAgent',
    
    # Агенты
    'DossierAnalysisAgent',
    'CarInterestAnalysisAgent', 
    'TaskAnalysisAgent',
    
    # Состояния
    'DossierAnalysisState',
    'CarInterestAnalysisState',
    'TaskAnalysisState',
    
    # Экземпляры агентов
    'dossier_agent',
    'car_interest_agent',
    'task_agent',
    
    # Workflows
    'ClientAnalysisWorkflow',
    
    # Схемы
    'DOSSIER_SCHEMA',
    'TASK_SCHEMA', 
    'CAR_INTEREST_SCHEMA',
    
    # Инструменты
    'DOSSIER_TOOLS',
    'CAR_INTEREST_TOOLS',
    'TASK_TOOLS',
    
    # Уведомления (для обратной совместимости)
    'send_dossier_notification',
    'send_car_interest_notification', 
    'send_task_notification',
    'sync_send_dossier_notification',
    'sync_send_car_interest_notification',
    'sync_send_task_notification',
    
    # Таймеры
    'analysis_timers'
] 