from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas import dossier as dossier_schemas
from ..services.dossier_service import DossierService
from ..services.client_service import ClientService

router = APIRouter()


@router.get("/client/{client_id}", response_model=dossier_schemas.Dossier)
def get_dossier_by_client(client_id: int, db: Session = Depends(get_db)):
    """Получить досье клиента"""
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    dossier = DossierService.get_dossier_by_client(db, client_id=client_id)
    if dossier is None:
        raise HTTPException(status_code=404, detail="Досье не найдено")
    return dossier


@router.get("/{dossier_id}", response_model=dossier_schemas.Dossier)
def get_dossier(dossier_id: int, db: Session = Depends(get_db)):
    """Получить досье по ID"""
    dossier = DossierService.get_dossier(db, dossier_id=dossier_id)
    if dossier is None:
        raise HTTPException(status_code=404, detail="Досье не найдено")
    return dossier


@router.post("/", response_model=dossier_schemas.Dossier)
def create_dossier(dossier: dossier_schemas.DossierCreate, db: Session = Depends(get_db)):
    """Создать новое досье"""
    # Проверяем, что клиент существует
    client = ClientService.get_client(db, dossier.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Проверяем, что досье еще не существует
    existing_dossier = DossierService.get_dossier_by_client(db, dossier.client_id)
    if existing_dossier:
        raise HTTPException(status_code=400, detail="Досье для этого клиента уже существует")
    
    return DossierService.create_dossier(db=db, dossier=dossier)


@router.put("/{dossier_id}", response_model=dossier_schemas.Dossier)
def update_dossier(
    dossier_id: int, 
    dossier_update: dossier_schemas.DossierUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить досье"""
    dossier = DossierService.update_dossier(db, dossier_id=dossier_id, dossier_update=dossier_update)
    if dossier is None:
        raise HTTPException(status_code=404, detail="Досье не найдено")
    return dossier


@router.put("/client/{client_id}", response_model=dossier_schemas.Dossier)
def update_or_create_dossier_by_client(
    client_id: int,
    summary: str,
    db: Session = Depends(get_db)
):
    """Обновить или создать досье для клиента"""
    client = ClientService.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    return DossierService.update_or_create_dossier(db, client_id=client_id, summary=summary)