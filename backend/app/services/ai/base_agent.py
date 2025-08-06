"""Базовый класс для всех AI агентов анализа"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, TypedDict, Optional, Literal
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import SessionLocal
from ...models.message import Message

logger = logging.getLogger(__name__)

# Настройка LangSmith трейсинга если доступно
if settings.langchain_api_key and settings.langchain_tracing_v2:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    if settings.langchain_endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    if settings.langchain_project:
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    logger.info(f"LangSmith трейсинг включен для проекта: {settings.langchain_project}")


class BaseAnalysisAgent:
    """Базовый класс для всех агентов анализа"""
    
    def __init__(self, tools: List, state_class):
        self.tools = tools
        self.state_class = state_class
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0.3  # Низкая температура для предсказуемого вызова tools
        ).bind_tools(self.tools)
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Создает граф для tool calling агента"""
        workflow = StateGraph(self.state_class)
        
        # Добавляем узлы
        workflow.add_node("prepare_context", self._prepare_context)
        workflow.add_node("agent_loop", self._agent_loop)  # Основной цикл агента
        workflow.add_node("process_updates", self._process_updates)
        
        # Определяем последовательность
        workflow.set_entry_point("prepare_context")
        workflow.add_edge("prepare_context", "agent_loop")
        workflow.add_edge("agent_loop", "process_updates")
        workflow.add_edge("process_updates", END)
        
        return workflow.compile()
    
    
    def _agent_loop(self, state) -> dict:
        """Основной цикл агента для tool calling с retry логикой"""
        try:
            client_id = state["client_id"]
            logger.info(f"Запуск агента для клиента {client_id}")
            
            # Генерируем system prompt
            system_prompt = self._generate_system_prompt(state)
            
            # Подготавливаем сообщения: сначала история, потом system prompt
            messages = state["messages"] + [
                SystemMessage(content=system_prompt)
            ]
            
            # Максимальное количество итераций для безопасности
            max_iterations = 10
            iteration = 0
            
            # Флаг завершения (когда вызван confirm_all)
            is_confirmed = False
            
            while iteration < max_iterations and not is_confirmed:
                iteration += 1
                logger.info(f"Итерация {iteration} для клиента {client_id}")
                
                # Вызываем LLM с retry логикой
                response = self._invoke_llm_with_retry(messages)
                if response is None:
                    error_msg = "Не удалось получить ответ от LLM после нескольких попыток"
                    logger.error(error_msg)
                    state["errors"].append(error_msg)
                    break
                    
                messages.append(response)
                
                # Проверяем, есть ли tool calls
                if hasattr(response, "tool_calls") and response.tool_calls:
                    # Проверяем, есть ли confirm_all среди вызовов
                    for tool_call in response.tool_calls:
                        if tool_call["name"].startswith("confirm_all"):
                            is_confirmed = True
                    
                    # Выполняем tool calls с обработкой ошибок
                    tool_results = self._execute_tool_calls_with_retry(state, response.tool_calls)
                    
                    # Добавляем результаты в историю
                    messages.extend(tool_results)
                    
                    # Если были ошибки валидации, даем агенту шанс исправить
                    has_validation_errors = any(
                        "validation error" in msg.content.lower() 
                        for msg in tool_results 
                        if isinstance(msg, ToolMessage)
                    )
                    
                    if has_validation_errors and iteration < max_iterations - 1:
                        logger.info(f"Обнаружены ошибки валидации, даем агенту возможность исправить")
                        continue
                    
                    # Если не подтверждено, продолжаем цикл
                    if not is_confirmed:
                        continue
                else:
                    # Если нет tool calls, завершаем
                    logger.warning(f"Агент не вызвал инструменты на итерации {iteration}")
                    break
            
            # Сохраняем финальную историю сообщений
            state["messages"] = messages
            
            if iteration >= max_iterations:
                error_msg = f"Достигнут лимит итераций ({max_iterations})"
                logger.error(error_msg)
                state["errors"].append(error_msg)
            
        except Exception as e:
            error_msg = f"Ошибка в agent_loop: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _format_chat_messages(self, chat_messages: List[Message]) -> List[BaseMessage]:
        """Форматирует сообщения чата с временными метками и указанием отправителя"""
        formatted_messages = []
        for msg in chat_messages:
            timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S") if msg.timestamp else "unknown"
            sender = "human" if msg.sender.value == "client" else "assistant"
            sender_label = "КЛИЕНТ" if msg.sender.value == "client" else "ФЕРМЕР"
            
            if msg.content_type != "text":
                content = f"[{timestamp}] [{sender_label}] [{msg.content_type.upper()}] {msg.content}"
            else:
                content = f"[{timestamp}] [{sender_label}] {msg.content}"
            
            if sender == "human":
                formatted_messages.append(HumanMessage(content=content))
            else:
                formatted_messages.append(AIMessage(content=content))
        
        return formatted_messages
    
    def _invoke_llm_with_retry(self, messages: List[BaseMessage], max_retries: int = 3) -> Optional[AIMessage]:
        """Вызывает LLM с retry логикой для обработки временных ошибок"""
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Экспоненциальная задержка: 1, 2, 4 секунды
                    logger.warning(f"Ошибка вызова LLM (попытка {attempt + 1}/{max_retries}): {e}. Повтор через {wait_time}с")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Не удалось вызвать LLM после {max_retries} попыток: {e}")
                    return None
        return None
    
    def _execute_tool_calls_with_retry(self, state, tool_calls) -> List[ToolMessage]:
        """Выполняет вызовы инструментов с обработкой ошибок и возможностью retry"""
        tools_map = {tool.name: tool for tool in self.tools}
        tool_messages = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call.get("id", f"call_{len(state['messages'])}_{tool_name}")
            
            # Пробуем выполнить tool с retry для временных ошибок
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    if tool_name in tools_map:
                        # Выполняем инструмент
                        tool_result = tools_map[tool_name].invoke(tool_args)
                        
                        # Создаем ToolMessage с результатом
                        tool_message = ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call_id
                        )
                        tool_messages.append(tool_message)
                        
                        logger.info(f"Выполнен инструмент {tool_name}: {tool_result}")
                        break  # Успешно выполнено, выходим из retry цикла
                    else:
                        error_msg = f"Инструмент {tool_name} не найден"
                        tool_message = ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_call_id
                        )
                        tool_messages.append(tool_message)
                        state["errors"].append(error_msg)
                        break  # Не нужно retry для несуществующих tools
                        
                except Exception as e:
                    error_str = str(e)
                    
                    # Проверяем тип ошибки
                    is_validation_error = "validation error" in error_str.lower()
                    is_temporary_error = any(err in error_str.lower() for err in ["timeout", "connection", "rate limit"])
                    
                    if is_validation_error:
                        # Ошибки валидации не требуют retry - агент должен исправить параметры
                        error_msg = f"Ошибка валидации в {tool_name}: {error_str}"
                        tool_message = ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_call_id
                        )
                        tool_messages.append(tool_message)
                        logger.warning(error_msg)
                        break
                    
                    elif is_temporary_error and attempt < max_retries - 1:
                        # Временные ошибки - делаем retry
                        wait_time = 1 * (attempt + 1)
                        logger.warning(f"Временная ошибка в {tool_name}: {error_str}. Повтор через {wait_time}с")
                        time.sleep(wait_time)
                        continue
                    
                    else:
                        # Постоянная ошибка или последняя попытка
                        error_msg = f"Ошибка выполнения инструмента {tool_name}: {error_str}"
                        tool_message = ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_call_id
                        )
                        tool_messages.append(tool_message)
                        state["errors"].append(error_msg)
                        logger.error(error_msg)
                        break
        
        return tool_messages
    
    # Абстрактные методы которые должны быть реализованы в подклассах
    def _prepare_context(self, state) -> dict:
        """Подготовка контекста - должен быть реализован в подклассе"""
        raise NotImplementedError
    
    def _process_updates(self, state) -> dict:
        """Обработка обновлений - должен быть реализован в подклассе"""
        raise NotImplementedError
    
    def _generate_system_prompt(self, state) -> str:
        """Генерация system prompt - должен быть реализован в подклассе"""
        raise NotImplementedError
    
    def analyze(self, client_id: int, client_name: str, chat_messages: List[Message]) -> Dict[str, Any]:
        """Базовый метод анализа - должен быть переопределен в подклассе"""
        raise NotImplementedError 