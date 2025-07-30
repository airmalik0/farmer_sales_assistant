import httpx
import asyncio
from typing import Optional, Dict, Any
from config import BACKEND_URL


class APIClient:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def get_or_create_client(self, telegram_id: int, first_name: str = None, 
                                 last_name: str = None, username: str = None) -> Optional[Dict[Any, Any]]:
        """Получить или создать клиента"""
        try:
            # Сначала пытаемся найти клиента
            response = await self.client.get(f"{self.base_url}/api/v1/clients/telegram/{telegram_id}")
            if response.status_code == 200:
                return response.json()
            
            # Если не найден, создаем нового
            client_data = {
                "telegram_id": telegram_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username
            }
            response = await self.client.post(f"{self.base_url}/api/v1/clients/", json=client_data)
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            print(f"Ошибка при работе с клиентом: {e}")
        
        return None

    async def create_message(self, client_id: int, sender: str, content_type: str, content: str) -> Optional[Dict[Any, Any]]:
        """Создать новое сообщение"""
        try:
            message_data = {
                "client_id": client_id,
                "sender": sender,
                "content_type": content_type,
                "content": content
            }
            response = await self.client.post(f"{self.base_url}/api/v1/messages/", json=message_data)
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"Ошибка при создании сообщения: {e}")
        
        return None

    async def get_all_clients(self) -> list:
        """Получить всех клиентов для рассылки"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/clients/")
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"Ошибка при получении клиентов: {e}")
        
        return []

    async def farmer_broadcast(self, content_type: str, content: str, include_greeting: bool = True) -> Optional[Dict[Any, Any]]:
        """Массовая рассылка от фермера через API"""
        try:
            broadcast_data = {
                "content_type": content_type,
                "content": content,
                "include_greeting": include_greeting
            }
            response = await self.client.post(f"{self.base_url}/api/v1/telegram/broadcast", json=broadcast_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                # Обрабатываем структурированные ошибки API
                return self._handle_api_error(response)
                
        except Exception as e:
            print(f"Ошибка при рассылке через API: {e}")
            return {
                "success": False,
                "error": "network_error", 
                "message": f"❌ Ошибка сети: {str(e)}"
            }
        
        return None

    async def validate_broadcast_clients(self) -> Optional[Dict[Any, Any]]:
        """Проверить готовность клиентов к рассылке"""
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/telegram/validate-broadcast")
            if response.status_code == 200:
                return response.json()
            else:
                # Обрабатываем ошибки валидации
                return self._handle_api_error(response)
                
        except Exception as e:
            print(f"Ошибка при проверке клиентов: {e}")
            return {
                "total_clients": 0,
                "clients_ready": 0,
                "clients_without_names": [],
                "clients_with_unapproved_names": [],
                "can_broadcast": False
            }
    
    def _handle_api_error(self, response) -> Dict[str, Any]:
        """Обрабатывает ошибки API и возвращает понятные сообщения"""
        try:
            error_data = response.json()
            
            # Если это структурированная ошибка
            if isinstance(error_data, dict) and "error" in error_data:
                error_info = error_data["error"]
                error_code = error_info.get("code", "UNKNOWN")
                error_message = error_info.get("message", "Неизвестная ошибка")
                error_details = error_info.get("details", {})
                
                # Создаем понятные сообщения для пользователя
                user_message = self._create_user_friendly_message(error_code, error_message, error_details)
                
                return {
                    "success": False,
                    "error": error_code.lower(),
                    "message": user_message
                }
            
            # Если это простая ошибка с detail
            elif isinstance(error_data, dict) and "detail" in error_data:
                detail = error_data["detail"]
                
                # Если detail тоже структурированная ошибка
                if isinstance(detail, dict) and "error" in detail:
                    error_info = detail["error"]
                    error_code = error_info.get("code", "UNKNOWN")
                    error_message = error_info.get("message", "Неизвестная ошибка")
                    error_details = error_info.get("details", {})
                    
                    user_message = self._create_user_friendly_message(error_code, error_message, error_details)
                    
                    return {
                        "success": False,
                        "error": error_code.lower(),
                        "message": user_message
                    }
                else:
                    # Простое текстовое сообщение
                    return {
                        "success": False,
                        "error": "api_error",
                        "message": f"❌ Ошибка: {detail}"
                    }
            
        except Exception as e:
            print(f"Ошибка при обработке ответа API: {e}")
        
        # Fallback для неструктурированных ошибок
        return {
            "success": False,
            "error": "api_error",
            "message": f"❌ Ошибка сервера (код: {response.status_code})"
        }
    
    def _create_user_friendly_message(self, error_code: str, error_message: str, error_details: dict) -> str:
        """Создает понятное сообщение для пользователя на основе кода ошибки"""
        
        if error_code == "NO_CLIENTS":
            return (
                "❌ <b>Рассылка невозможна</b>\n\n"
                "🔍 <b>Причина:</b> В системе нет зарегистрированных клиентов\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Клиенты регистрируются автоматически при первом сообщении боту\n"
                "• Пригласите пользователей написать боту\n"
                "• Или подождите, пока клиенты сами обратятся"
            )
        
        elif error_code == "CLIENTS_NOT_APPROVED":
            unapproved_count = error_details.get("clients_with_unapproved_names", 0)
            without_names_count = error_details.get("clients_without_names", 0)
            
            issues = []
            if without_names_count > 0:
                issues.append(f"• {without_names_count} клиент(ов) без имени")
            if unapproved_count > 0:
                issues.append(f"• {unapproved_count} клиент(ов) с неодобренными именами")
            
            return (
                "❌ <b>Рассылка заблокирована</b>\n\n"
                "🔍 <b>Проблемы:</b>\n" + "\n".join(issues) + "\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Перейдите в веб-панель управления\n"
                "• Одобрите имена всех клиентов\n"
                "• После этого рассылка станет доступна"
            )
        
        elif error_code == "BROADCAST_FAILED":
            suggestion = error_details.get("suggestion", "Повторите попытку позже")
            return (
                "❌ <b>Ошибка рассылки</b>\n\n"
                f"🔍 <b>Причина:</b> {error_message}\n\n"
                f"💡 <b>Рекомендация:</b> {suggestion}"
            )
        
        else:
            # Общий формат для неизвестных ошибок
            suggestion = error_details.get("suggestion", "Обратитесь к администратору")
            return (
                f"❌ <b>Ошибка:</b> {error_message}\n\n"
                f"💡 <b>Рекомендация:</b> {suggestion}"
            )

    async def get_greeting(self) -> Optional[Dict[Any, Any]]:
        """Получить текущее приветствие"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/settings/greeting")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Ошибка при получении приветствия: {e}")
        return None

    async def set_greeting(self, greeting_text: str, enabled: bool = True) -> Optional[Dict[Any, Any]]:
        """Установить приветствие"""
        try:
            data = {
                "greeting_text": greeting_text,
                "enabled": enabled
            }
            response = await self.client.post(f"{self.base_url}/api/v1/settings/greeting", json=data)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Ошибка при установке приветствия: {e}")
        return None

    async def update_greeting(self, greeting_text: str = None, enabled: bool = None) -> Optional[Dict[Any, Any]]:
        """Обновить приветствие"""
        try:
            data = {}
            if greeting_text is not None:
                data["greeting_text"] = greeting_text
            if enabled is not None:
                data["enabled"] = enabled
            
            response = await self.client.put(f"{self.base_url}/api/v1/settings/greeting", json=data)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Ошибка при обновлении приветствия: {e}")
        return None

    async def clear_greeting(self) -> bool:
        """Очистить приветствие"""
        try:
            response = await self.client.delete(f"{self.base_url}/api/v1/settings/greeting")
            return response.status_code == 200
        except Exception as e:
            print(f"Ошибка при очистке приветствия: {e}")
        return False

    async def send_message_to_client(self, telegram_id: int, message: str) -> bool:
        """Отправляет сообщение клиенту через API (заглушка для будущей интеграции)"""
        # Здесь будет логика отправки сообщения через бота
        # Пока возвращаем True как успешную отправку
        return True