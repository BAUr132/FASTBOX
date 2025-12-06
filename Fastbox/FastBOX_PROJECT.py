import time
import json
import requests
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Set

# ==============================
# НАСТРОЙКИ
# ==============================

BOT_TOKEN = "8571414658:AAG3-A-zzxoBIqxt9FqGewSKViHk5rSCtg0"  # <-- ВСТАВЬ СВОЙ ТОКЕН
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# ВАЖНО: здесь впиши свой Telegram ID, чтобы быть админом
# Узнать свой ID можно через @userinfobot или @getmyid_bot
ADMIN_IDS: Set[int] = {7041571370}

# Здесь можно добавить ID курьеров (или ты сам будешь и админом, и курьером):
COURIER_IDS: Set[int] = {1477089022}

# ==============================
# МОДЕЛИ
# ==============================


class OrderType(str, Enum):
    THINGS = "Вещи"
    FOOD = "Еда"
    GROCERIES = "Продукты"
    MEDICINE = "Лекарства"


class OrderStatus(str, Enum):
    CREATED = "Создан"
    SCHEDULED = "Запланирован"
    COURIER_ASSIGNED = "Курьер назначен"
    COURIER_TO_SENDER = "Курьер едет к отправителю"
    PICKED_UP = "Посылка у курьера"
    COURIER_TO_RECEIVER = "Курьер в пути к получателю"
    DELIVERED = "Доставлено"
    CANCELLED = "Отменено"


@dataclass
class Order:
    id: int
    user_id: int
    order_type: OrderType
    city_from: str
    from_address: str
    city_to: str
    to_address: str
    weight_kg: float
    comment: str
    scheduled_date: Optional[str] = None  # YYYY-MM-DD
    time_window: Optional[str] = None     # "14:00-16:00"
    price_kzt: int = 0
    status: OrderStatus = OrderStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    courier_id: Optional[int] = None      # кто взял заказ


# ==============================
# "БАЗА ДАННЫХ" В ПАМЯТИ
# ==============================

orders_store: Dict[int, Order] = {}
user_orders_index: Dict[int, List[int]] = {}
order_counter: int = 1

# Стейты диалога по пользователям
user_state: Dict[int, str] = {}
temp_order_data: Dict[int, Dict] = {}

# ==============================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================


def send_request(method: str, params: dict = None):
    url = BASE_URL + method
    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            print("Telegram API error:", data)
        return data
    except Exception as e:
        print("HTTP error:", e)
        return None

