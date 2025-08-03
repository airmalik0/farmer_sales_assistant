"""Базовый класс для всех AI агентов анализа"""

import logging
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


class BaseAnalysisAgent:
    """Базовый класс для всех агентов анализа"""
    
    def __init__(self, tools: List, state_class):
        self.tools = tools
        self.state_class = state_class
        self.llm = ChatOpenAI(
            model="o4-mini",
            api_key=settings.openai_api_key,
            temperature=1
        ).bind_tools(self.tools)
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Создает базовый граф анализа с ReACT паттерном"""
        workflow = StateGraph(self.state_class)
        
        # Добавляем узлы
        workflow.add_node("prepare_context", self._prepare_context)
        workflow.add_node("analyze", self._analyze)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("process_updates", self._process_updates)
        
        # Определяем последовательность
        workflow.set_entry_point("prepare_context")
        workflow.add_edge("prepare_context", "analyze")
        
        # Условная маршрутизация после анализа (ReACT паттерн)
        def route_after_analyze(state):
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                # Проверяем есть ли confirm_all среди вызовов
                for tool_call in last_message.tool_calls:
                    if tool_call["name"].startswith("confirm_all"):
                        return "process_updates"
                return "execute_tools"
            return "process_updates"
        
        # После выполнения tools возвращаемся к analyze для следующего цикла ReACT
        def route_after_tools(state):
            return "analyze"
        
        workflow.add_conditional_edges("analyze", route_after_analyze)
        workflow.add_conditional_edges("execute_tools", route_after_tools)
        workflow.add_edge("process_updates", END)
        
        return workflow.compile()
    
    def _execute_tools(self, state) -> dict:
        """Выполнение инструментов и добавление результатов в историю сообщений"""
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # Создаем маппинг инструментов по именам
            tools_map = {tool.name: tool for tool in self.tools}
            
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call.get("id", f"call_{len(state['messages'])}")
                
                try:
                    if tool_name in tools_map:
                        # Выполняем инструмент
                        tool_result = tools_map[tool_name].invoke(tool_args)
                        
                        # Добавляем результат как ToolMessage
                        tool_message = ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call_id
                        )
                        state["messages"].append(tool_message)
                        
                        logger.info(f"Выполнен инструмент {tool_name}: {tool_result}")
                    else:
                        error_msg = f"Инструмент {tool_name} не найден"
                        tool_message = ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_call_id
                        )
                        state["messages"].append(tool_message)
                        state["errors"].append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Ошибка выполнения инструмента {tool_name}: {str(e)}"
                    tool_message = ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call_id
                    )
                    state["messages"].append(tool_message)
                    state["errors"].append(error_msg)
                    logger.error(error_msg)
        
        return state
    
    def _analyze(self, state) -> dict:
        """Анализ с использованием инструментов"""
        try:
            client_id = state["client_id"]
            logger.info(f"Анализ для клиента {client_id}")
            
            # Определяем, есть ли уже system message в истории
            has_system_message = any(
                isinstance(msg, SystemMessage)
                for msg in state["messages"]
            )
            
            if not has_system_message:
                # Первый вызов - создаем полную историю с system prompt
                system_prompt = self._generate_system_prompt(state)
                
                # Берем только оригинальные human/ai сообщения
                original_messages = [
                    msg for msg in state["messages"]
                    if isinstance(msg, (HumanMessage, AIMessage))
                ]
                
                # Добавляем system message и вызываем LLM
                messages_to_send = original_messages + [SystemMessage(content=system_prompt)]
                response = self.llm.invoke(messages_to_send)
                
                # Полностью обновляем state messages для правильной работы ReAct
                state["messages"] = messages_to_send + [response]
            else:
                # Последующие вызовы - просто вызываем LLM с текущей историей
                response = self.llm.invoke(state["messages"])
                state["messages"].append(response)
            
        except Exception as e:
            error_msg = f"Ошибка анализа: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
        
        return state
    
    def _format_chat_messages(self, chat_messages: List[Message]) -> List[BaseMessage]:
        """Форматирует сообщения чата с временными метками и указанием отправителя"""
        formatted_messages = []
        for msg in chat_messages:
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
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