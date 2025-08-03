"""JSON схемы для structured output OpenAI"""

# JSON схема для досье клиента
DOSSIER_SCHEMA = {
    "type": "object",
    "properties": {
        "client_info": {
            "type": "object",
            "properties": {
                "phone": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Номер телефона клиента"
                },
                "current_location": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Город или местоположение клиента"
                },
                "birthday": {
                    "anyOf": [{"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}, {"type": "null"}],
                    "description": "Дата рождения в формате YYYY-MM-DD"
                },
                "gender": {
                    "anyOf": [{"type": "string", "enum": ["male", "female"]}, {"type": "null"}],
                    "description": "Пол клиента: male или female"
                },
                "client_type": {
                    "anyOf": [{"type": "string", "enum": ["private", "reseller", "broker", "dealer", "transporter"]}, {"type": "null"}],
                    "description": "Тип клиента: private (частник), reseller (перекуп), broker (автоподборщик), dealer (дилер), transporter (перегонщик)"
                },
                "personal_notes": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Личные заметки о клиенте (семья, хобби, предпочтения)"
                },
                "business_profile": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Бизнес-профиль клиента (только для reseller, broker, dealer): специализация, объемы, требования"
                }
            },
            "required": ["phone", "current_location", "birthday", "gender", "client_type", "personal_notes", "business_profile"],
            "additionalProperties": False
        }
    },
    "required": ["client_info"],
    "additionalProperties": False
}

# JSON схема для задач
TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "description": "Список задач, которые нужно выполнить",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Четкое описание задачи"
                    },
                    "due_date": {
                        "anyOf": [{"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}, {"type": "null"}],
                        "description": "Дата выполнения задачи в формате YYYY-MM-DD. Null, если дата не определена."
                    },
                    "priority": {
                        "anyOf": [{"type": "string", "enum": ["low", "normal", "high"]}, {"type": "null"}],
                        "description": "Приоритет задачи: low, normal или high. По умолчанию normal."
                    }
                },
                "required": ["description", "due_date", "priority"],
                "additionalProperties": False
            }
        }
    },
    "required": ["tasks"],
    "additionalProperties": False
}

# JSON схема для автомобильных интересов
CAR_INTEREST_SCHEMA = {
    "type": "object",
    "properties": {
        "queries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "brand": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                            {"type": "null"}
                        ],
                        "description": "Марка автомобиля или массив марок"
                    },
                    "model": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                            {"type": "null"}
                        ],
                        "description": "Модель автомобиля или массив моделей"
                    },
                    "price_min": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Минимальная цена в долларах"
                    },
                    "price_max": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Максимальная цена в долларах"
                    },
                    "year_min": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Минимальный год выпуска"
                    },
                    "year_max": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Максимальный год выпуска"
                    },
                    "mileage_max": {
                        "anyOf": [
                            {"type": "number"},
                            {"type": "null"}
                        ],
                        "description": "Максимальный пробег в км"
                    },
                    "exterior_color": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                            {"type": "null"}
                        ],
                        "description": "Цвет кузова или массив цветов"
                    },
                    "interior_color": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                            {"type": "null"}
                        ],
                        "description": "Цвет салона или массив цветов"
                    }
                },
                "required": ["brand", "model", "price_min", "price_max", "year_min", "year_max", "mileage_max", "exterior_color", "interior_color"],
                "additionalProperties": False
            }
        }
    },
    "required": ["queries"],
    "additionalProperties": False
} 