from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..services.settings_service import SettingsService
from ..schemas.settings import (
    GreetingRequest, 
    GreetingResponse, 
    GreetingUpdateRequest,
    Setting,
    SettingCreate,
    SettingUpdate
)
from ..models.settings import GreetingSettings

router = APIRouter()


@router.get("/greeting", response_model=GreetingResponse)
def get_greeting(db: Session = Depends(get_db)):
    """Получить текущее приветствие"""
    custom_greeting = SettingsService.get_custom_greeting(db)
    enabled = SettingsService.is_custom_greeting_enabled(db)
    effective_greeting = SettingsService.get_effective_greeting(db)
    
    return GreetingResponse(
        greeting_text=effective_greeting,
        enabled=enabled,
        is_custom=enabled and bool(custom_greeting.strip())
    )


@router.put("/greeting", response_model=GreetingResponse)
def update_greeting(
    request: GreetingUpdateRequest,
    db: Session = Depends(get_db)
):
    """Обновить настройки приветствия"""
    try:
        # Обновляем текст приветствия если передан
        if request.greeting_text is not None:
            SettingsService.set_custom_greeting(db, request.greeting_text)
        
        # Обновляем статус включения если передан
        if request.enabled is not None:
            SettingsService.set_custom_greeting_enabled(db, request.enabled)
        
        # Возвращаем актуальные данные
        custom_greeting = SettingsService.get_custom_greeting(db)
        enabled = SettingsService.is_custom_greeting_enabled(db)
        effective_greeting = SettingsService.get_effective_greeting(db)
        
        return GreetingResponse(
            greeting_text=effective_greeting,
            enabled=enabled,
            is_custom=enabled and bool(custom_greeting.strip())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении приветствия: {str(e)}")


@router.post("/greeting", response_model=GreetingResponse)
def set_greeting(
    request: GreetingRequest,
    db: Session = Depends(get_db)
):
    """Установить новое приветствие"""
    try:
        # Устанавливаем новое приветствие
        SettingsService.set_custom_greeting(db, request.greeting_text)
        SettingsService.set_custom_greeting_enabled(db, request.enabled)
        
        # Возвращаем результат
        effective_greeting = SettingsService.get_effective_greeting(db)
        
        return GreetingResponse(
            greeting_text=effective_greeting,
            enabled=request.enabled,
            is_custom=request.enabled and bool(request.greeting_text.strip())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при установке приветствия: {str(e)}")


@router.delete("/greeting")
def clear_greeting(db: Session = Depends(get_db)):
    """Очистить кастомное приветствие"""
    try:
        SettingsService.clear_custom_greeting(db)
        return {"message": "Кастомное приветствие очищено"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке приветствия: {str(e)}")


@router.get("/greeting/preview")
def preview_greeting(
    greeting_text: str,
    first_name: str = "Иван",
    last_name: str = "Иванов",
    db: Session = Depends(get_db)
):
    """Предпросмотр приветствия с подстановкой переменных"""
    from ..api.telegram import replace_greeting_variables
    
    preview = replace_greeting_variables(greeting_text, first_name, last_name)
    
    return {
        "original": greeting_text,
        "preview": preview,
        "variables": {
            "first_name": first_name,
            "last_name": last_name
        }
    }


# Дополнительные эндпоинты для работы с любыми настройками
@router.get("/{key}")
def get_setting(key: str, db: Session = Depends(get_db)):
    """Получить настройку по ключу"""
    setting = SettingsService.get_setting(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Настройка не найдена")
    
    return {
        "key": setting.key,
        "value": setting.value,
        "description": setting.description,
        "is_active": setting.is_active
    }


@router.put("/{key}")
def update_setting(
    key: str,
    request: SettingUpdate,
    db: Session = Depends(get_db)
):
    """Обновить настройку"""
    setting = SettingsService.get_setting(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Настройка не найдена")
    
    if request.value is not None:
        setting.value = request.value
    if request.description is not None:
        setting.description = request.description
    if request.is_active is not None:
        setting.is_active = request.is_active
    
    db.commit()
    db.refresh(setting)
    
    return {
        "key": setting.key,
        "value": setting.value,
        "description": setting.description,
        "is_active": setting.is_active
    } 