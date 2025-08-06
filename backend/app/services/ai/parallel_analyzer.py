"""Параллельный анализатор для запуска нескольких агентов одновременно"""

import asyncio
import logging
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...models.message import Message
from .task_agent import task_agent
from .dossier_agent import dossier_agent
from .car_interest_agent import car_interest_agent

logger = logging.getLogger(__name__)


class ParallelAnalyzer:
    """Запускает агентов параллельно для ускорения обработки"""
    
    def __init__(self, max_workers: int = 3):
        """
        Args:
            max_workers: Максимальное количество параллельных потоков
        """
        self.max_workers = max_workers
    
    def analyze_all(
        self,
        client_id: int,
        client_name: str,
        chat_messages: List[Message],
        agents_to_run: List[str] = None
    ) -> Dict[str, Any]:
        """
        Запускает анализ всеми агентами параллельно
        
        Args:
            client_id: ID клиента
            client_name: Имя клиента
            chat_messages: История сообщений
            agents_to_run: Список агентов для запуска (по умолчанию все)
        
        Returns:
            Словарь с результатами всех агентов
        """
        if agents_to_run is None:
            agents_to_run = ["task", "dossier", "car_interest"]
        
        results = {}
        errors = {}
        
        # Подготавливаем задачи для выполнения
        agent_tasks = {}
        
        if "task" in agents_to_run:
            agent_tasks["task"] = lambda: task_agent.analyze(client_id, client_name, chat_messages)
        
        if "dossier" in agents_to_run:
            agent_tasks["dossier"] = lambda: dossier_agent.analyze(client_id, client_name, chat_messages)
        
        if "car_interest" in agents_to_run:
            agent_tasks["car_interest"] = lambda: car_interest_agent.analyze(client_id, client_name, chat_messages)
        
        # Запускаем агентов параллельно
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(agent_tasks))) as executor:
            # Создаем futures для каждого агента
            future_to_agent = {
                executor.submit(task): agent_name
                for agent_name, task in agent_tasks.items()
            }
            
            # Обрабатываем результаты по мере готовности
            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    result = future.result(timeout=30)  # 30 секунд таймаут на агента
                    results[agent_name] = result
                    logger.info(f"Агент {agent_name} успешно завершил анализ")
                except Exception as e:
                    error_msg = f"Ошибка в агенте {agent_name}: {str(e)}"
                    logger.error(error_msg)
                    errors[agent_name] = error_msg
                    results[agent_name] = {
                        "error": str(e),
                        "confirmed": False
                    }
        
        # Возвращаем объединенный результат
        return {
            "results": results,
            "errors": errors,
            "all_confirmed": all(
                r.get("confirmed", False) for r in results.values()
            )
        }
    
    async def analyze_all_async(
        self,
        client_id: int,
        client_name: str,
        chat_messages: List[Message],
        agents_to_run: List[str] = None
    ) -> Dict[str, Any]:
        """
        Асинхронная версия для использования в async контексте
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.analyze_all,
            client_id,
            client_name,
            chat_messages,
            agents_to_run
        )


# Глобальный экземпляр для использования
parallel_analyzer = ParallelAnalyzer()