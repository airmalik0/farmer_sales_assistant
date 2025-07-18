from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine
from .models import Client, Message, Dossier
from .api import api_router

# Создаем таблицы
Client.metadata.create_all(bind=engine)
Message.metadata.create_all(bind=engine)
Dossier.metadata.create_all(bind=engine)

app = FastAPI(
    title="Farmer CRM API",
    description="API для CRM-системы Фермер",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Farmer CRM API v1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}