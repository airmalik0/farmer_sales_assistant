from sqlalchemy.orm import Session
from typing import Optional
from ..models.settings import Settings, GreetingSettings


class SettingsService:
    @staticmethod
    def get_setting(db: Session, key: str) -> Optional[Settings]:
        """Получить настройку по ключу"""
        return db.query(Settings).filter(
            Settings.key == key,
            Settings.is_active == True
        ).first()
    
    @staticmethod
    def get_setting_value(db: Session, key: str, default: str = "") -> str:
        """Получить значение настройки или дефолтное значение"""
        setting = SettingsService.get_setting(db, key)
        return setting.value if setting else default
    
    @staticmethod
    def set_setting(db: Session, key: str, value: str, description: str = "") -> Settings:
        """Установить значение настройки"""
        setting = SettingsService.get_setting(db, key)
        
        if setting:
            # Обновляем существующую настройку
            setting.value = value
            if description:
                setting.description = description
        else:
            # Создаем новую настройку
            setting = Settings(
                key=key,
                value=value,
                description=description,
                is_active=True
            )
            db.add(setting)
        
        db.commit()
        db.refresh(setting)
        return setting
    
    @staticmethod
    def get_custom_greeting(db: Session) -> str:
        """Получить кастомное приветствие"""
        return SettingsService.get_setting_value(
            db, 
            GreetingSettings.CUSTOM_GREETING_KEY, 
            ""
        )
    
    @staticmethod
    def set_custom_greeting(db: Session, greeting: str) -> Settings:
        """Установить кастомное приветствие"""
        return SettingsService.set_setting(
            db,
            GreetingSettings.CUSTOM_GREETING_KEY,
            greeting,
            "Кастомное приветствие для рассылок"
        )
    
    @staticmethod
    def is_custom_greeting_enabled(db: Session) -> bool:
        """Проверить, включено ли кастомное приветствие"""
        value = SettingsService.get_setting_value(
            db,
            GreetingSettings.USE_CUSTOM_GREETING_KEY,
            "false"
        )
        return value.lower() == "true"
    
    @staticmethod
    def set_custom_greeting_enabled(db: Session, enabled: bool) -> Settings:
        """Включить/выключить кастомное приветствие"""
        return SettingsService.set_setting(
            db,
            GreetingSettings.USE_CUSTOM_GREETING_KEY,
            "true" if enabled else "false",
            "Использовать кастомное приветствие"
        )
    
    @staticmethod
    def get_effective_greeting(db: Session) -> str:
        """Получить активное приветствие (кастомное или дефолтное)"""
        if SettingsService.is_custom_greeting_enabled(db):
            custom_greeting = SettingsService.get_custom_greeting(db)
            if custom_greeting.strip():
                return custom_greeting
        
        return GreetingSettings.get_default_greeting()
    
    @staticmethod
    def clear_custom_greeting(db: Session) -> Settings:
        """Очистить кастомное приветствие"""
        # Очищаем текст приветствия
        SettingsService.set_custom_greeting(db, "")
        # Отключаем использование кастомного приветствия
        return SettingsService.set_custom_greeting_enabled(db, False) 