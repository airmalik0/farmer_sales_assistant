from fastapi import HTTPException
from typing import Dict, Any


class BroadcastError(Exception):
    """Базовое исключение для ошибок рассылки"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NoClientsError(BroadcastError):
    """Ошибка: нет клиентов для рассылки"""
    def __init__(self):
        super().__init__(
            "В системе нет зарегистрированных клиентов",
            {"error_code": "NO_CLIENTS", "suggestion": "Добавьте клиентов через Telegram бота"}
        )


class ClientsNotApprovedError(BroadcastError):
    """Ошибка: не все клиенты одобрены для рассылки"""
    def __init__(self, unapproved_count: int, without_names_count: int):
        message = "Не все клиенты готовы к рассылке"
        details = {
            "error_code": "CLIENTS_NOT_APPROVED",
            "unapproved_count": unapproved_count,
            "without_names_count": without_names_count,
            "suggestion": "Одобрите имена клиентов в веб-панели управления"
        }
        super().__init__(message, details)


class APIErrorResponse:
    """Стандартизированный формат ответов API с ошибками"""
    
    @staticmethod
    def create_error_response(error_code: str, message: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Создает стандартизированный ответ об ошибке"""
        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {}
            }
        }
    
    @staticmethod
    def no_clients_error() -> Dict[str, Any]:
        """Ошибка: нет клиентов"""
        return APIErrorResponse.create_error_response(
            "NO_CLIENTS",
            "В системе нет зарегистрированных клиентов",
            {
                "suggestion": "Клиенты автоматически регистрируются при первом сообщении боту",
                "action_required": "Напишите боту или пригласите пользователей"
            }
        )
    
    @staticmethod
    def clients_not_approved_error(unapproved_names: int, without_names: int) -> Dict[str, Any]:
        """Ошибка: клиенты не одобрены"""
        return APIErrorResponse.create_error_response(
            "CLIENTS_NOT_APPROVED",
            "Рассылка заблокирована: не все имена клиентов одобрены",
            {
                "clients_with_unapproved_names": unapproved_names,
                "clients_without_names": without_names,
                "suggestion": "Перейдите в веб-панель для одобрения имен клиентов",
                "action_required": "Одобрите имена всех клиентов перед рассылкой"
            }
        )


def handle_broadcast_error(error: Exception) -> HTTPException:
    """Преобразует ошибки рассылки в HTTP исключения"""
    if isinstance(error, NoClientsError):
        return HTTPException(
            status_code=422,
            detail=APIErrorResponse.no_clients_error()
        )
    elif isinstance(error, ClientsNotApprovedError):
        return HTTPException(
            status_code=400,
            detail=APIErrorResponse.clients_not_approved_error(
                error.details.get("unapproved_count", 0),
                error.details.get("without_names_count", 0)
            )
        )
    else:
        return HTTPException(
            status_code=500,
            detail=APIErrorResponse.create_error_response(
                "INTERNAL_ERROR",
                f"Внутренняя ошибка сервера: {str(error)}"
            )
        ) 