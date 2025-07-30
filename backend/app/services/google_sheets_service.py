import os
import logging
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..core.config import settings
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class CarData:
    """Класс для представления данных об автомобиле из Google Sheets"""
    def __init__(self, row_data: List[str], headers: List[str]):
        self.raw_data = dict(zip(headers, row_data))
        
    @property
    def car_id(self) -> Optional[str]:
        """ID автомобиля (например, GE-30)"""
        return self.raw_data.get(' STOCK #') or self.raw_data.get('id')
    
    @property
    def location(self) -> Optional[str]:
        """Локация автомобиля"""
        possible_keys = [' Прибытие в Поти', 'Location', 'локация', 'location']
        for key in possible_keys:
            if key in self.raw_data:
                return self.raw_data[key]
        return None
    
    @property
    def year(self) -> Optional[int]:
        """Год автомобиля"""
        year_str = self.raw_data.get('Год') or self.raw_data.get('Year')
        if year_str:
            try:
                return int(year_str)
            except ValueError:
                return None
        return None
    
    @property
    def brand(self) -> Optional[str]:
        """Марка автомобиля"""
        return self.raw_data.get('МАРКА') or self.raw_data.get('Brand')
    
    @property
    def model(self) -> Optional[str]:
        """Модель автомобиля"""
        return self.raw_data.get(' МОДЕЛЬ') or self.raw_data.get('Model')
    
    @property
    def price(self) -> Optional[float]:
        """Цена автомобиля"""
        price_str = self.raw_data.get(' ЦЕНА ПРОДАЖИ В ГРУЗИИ $') or self.raw_data.get('Price')
        if price_str:
            try:
                # Убираем символы валюты и пробелы
                clean_price = ''.join(filter(lambda x: x.isdigit() or x == '.', str(price_str)))
                return float(clean_price) if clean_price else None
            except ValueError:
                return None
        return None
    
    @property
    def mileage(self) -> Optional[int]:
        """Пробег автомобиля"""
        mileage_str = self.raw_data.get('Пробег') or self.raw_data.get('Mileage')
        if mileage_str:
            try:
                clean_mileage = ''.join(filter(str.isdigit, str(mileage_str)))
                return int(clean_mileage) if clean_mileage else None
            except ValueError:
                return None
        return None
    
    @property
    def status(self) -> Optional[str]:
        """Статус автомобиля"""
        return self.raw_data.get('Статус') or self.raw_data.get('Status')
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует данные в словарь"""
        return {
            'car_id': self.car_id,
            'location': self.location,
            'year': self.year,
            'brand': self.brand,
            'model': self.model,
            'price': self.price,
            'mileage': self.mileage,
            'status': self.status,
            'raw_data': self.raw_data
        }


class GoogleSheetsService:
    def __init__(self):
        self.service = None
        self.spreadsheet_id = settings.google_sheets_spreadsheet_id
        self.range_name = settings.google_sheets_range or "Sheet1!A:Z"
        
        # Проверяем наличие необходимых настроек
        if not self.spreadsheet_id or self.spreadsheet_id == "your_spreadsheet_id_here":
            logger.warning("Google Sheets Spreadsheet ID не настроен. Сервис Google Sheets будет отключен.")
            return
            
        self._connect()
    
    def _connect(self):
        """Подключение к Google Sheets API"""
        try:
            creds = None
            
            # Проверяем, что путь к файлу задан
            if not settings.google_sheets_credentials_file:
                logger.warning("Путь к файлу учетных данных Google Sheets не задан в переменных окружения")
                return
            
            # Проверяем существование файла с учетными данными
            if os.path.exists(settings.google_sheets_credentials_file):
                creds = ServiceCredentials.from_service_account_file(
                    settings.google_sheets_credentials_file,
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
            else:
                logger.warning(f"Файл учетных данных не найден: {settings.google_sheets_credentials_file}")
                return
            
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Успешно подключились к Google Sheets API")
            
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets API: {e}")
            self.service = None
    
    def is_connected(self) -> bool:
        """Проверяет, подключен ли сервис к Google Sheets"""
        return self.service is not None
    
    def get_sheet_data(self) -> List[CarData]:
        """Получает данные из Google Sheets и преобразует их в объекты CarData"""
        if not self.is_connected():
            logger.error("Нет подключения к Google Sheets")
            return []
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name
            ).execute()
            values = result.get('values', [])
            if not values:
                logger.warning("Google Sheets не содержит данных")
                return []
            
            # Первая строка - заголовки
            headers = values[0] if values else []
            car_data_list = []
            
            # Преобразуем каждую строку в объект CarData
            for row in values[1:]:
                # Дополняем строку пустыми значениями, если она короче заголовков
                padded_row = row + [''] * (len(headers) - len(row))
                car_data = CarData(padded_row, headers)
                car_data_list.append(car_data)
            
            logger.info(f"Получено {len(car_data_list)} записей из Google Sheets")
            return car_data_list
            
        except HttpError as error:
            logger.error(f"Ошибка при получении данных из Google Sheets: {error}")
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка при работе с Google Sheets: {e}")
            return []
    
    def get_car_by_id(self, car_id: str) -> Optional[CarData]:
        """Получает данные конкретного автомобиля по ID"""
        cars = self.get_sheet_data()
        for car in cars:
            if car.car_id == car_id:
                return car
        return None
    
    def filter_cars(self, **filters) -> List[CarData]:
        """Фильтрует автомобили по заданным критериям
        
        Args:
            brand: str или List[str] - марка или список марок
            model: str или List[str] - модель или список моделей  
            location: str - локация
            price_min: float - минимальная цена
            price_max: float - максимальная цена
            year_min: int - минимальный год
            year_max: int - максимальный год
            mileage_max: int - максимальный пробег
            status: str или List[str] - статус или список статусов
        """
        cars = self.get_sheet_data()
        filtered_cars = []
        
        for car in cars:
            match = True
            
            # Проверяем марку
            if 'brand' in filters and filters['brand']:
                brands = filters['brand'] if isinstance(filters['brand'], list) else [filters['brand']]
                if car.brand not in brands:
                    match = False
                    continue
            
            # Проверяем модель
            if 'model' in filters and filters['model']:
                models = filters['model'] if isinstance(filters['model'], list) else [filters['model']]
                if car.model not in models:
                    match = False
                    continue
            
            # Проверяем локацию
            if 'location' in filters and filters['location']:
                if car.location != filters['location']:
                    match = False
                    continue
            
            # Проверяем цену
            if 'price_min' in filters and filters['price_min'] is not None:
                if car.price is None or car.price < filters['price_min']:
                    match = False
                    continue
            
            if 'price_max' in filters and filters['price_max'] is not None:
                if car.price is None or car.price > filters['price_max']:
                    match = False
                    continue
            
            # Проверяем год
            if 'year_min' in filters and filters['year_min'] is not None:
                if car.year is None or car.year < filters['year_min']:
                    match = False
                    continue
            
            if 'year_max' in filters and filters['year_max'] is not None:
                if car.year is None or car.year > filters['year_max']:
                    match = False
                    continue
            
            # Проверяем пробег
            if 'mileage_max' in filters and filters['mileage_max'] is not None:
                if car.mileage is None or car.mileage > filters['mileage_max']:
                    match = False
                    continue
            
            # Проверяем статус
            if 'status' in filters and filters['status']:
                statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
                if car.status not in statuses:
                    match = False
                    continue
            
            if match:
                filtered_cars.append(car)
        
        return filtered_cars
    
    def get_headers(self) -> List[str]:
        """Получает заголовки столбцов из Google Sheets"""
        if not self.is_connected():
            return []
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="1:1"  # Только первая строка
            ).execute()
            
            values = result.get('values', [])
            return values[0] if values else []
            
        except Exception as e:
            logger.error(f"Ошибка при получении заголовков: {e}")
            return []


# Глобальный экземпляр сервиса
google_sheets_service = GoogleSheetsService() 