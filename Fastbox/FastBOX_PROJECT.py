import time
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
# Узнать свой ID можно через бота @userinfobot или @getmyid_bot
ADMIN_IDS: Set[int] = {7041571370}

# Если захочешь — сюда можно добавить ID курьеров
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


def get_updates(offset: Optional[int] = None):
    params = {"timeout": 50}
    if offset is not None:
        params["offset"] = offset
    data = send_request("getUpdates", params=params)
    if not data:
        return []
    return data.get("result", [])


def send_message(chat_id: int, text: str):
    send_request("sendMessage", {"chat_id": chat_id, "text": text})


def calculate_price_kzt(weight_kg: float, city_from: str, city_to: str, scheduled: bool) -> int:
    base = 1000
    per_kg = int(200 * max(weight_kg, 0.1))
    intercity = 500 if city_from.strip().lower() != city_to.strip().lower() else 0
    scheduled_extra = 300 if scheduled else 0
    return base + per_kg + intercity + scheduled_extra


def format_order(order: Order) -> str:
    return (
        f"📦 Заказ №{order.id}\n"
        f"Тип: {order.order_type.value}\n"
        f"Откуда: {order.city_from}, {order.from_address}\n"
        f"Куда: {order.city_to}, {order.to_address}\n"
        f"Вес: {order.weight_kg} кг\n"
        f"Дата: {order.scheduled_date or 'сегодня'}\n"
        f"Время: {order.time_window or 'как можно скорее'}\n"
        f"Комментарий: {order.comment or '-'}\n"
        f"Статус: {order.status.value}\n"
        f"Стоимость: {order.price_kzt} ₸"
    )


def reset_user_state(user_id: int):
    user_state.pop(user_id, None)
    temp_order_data.pop(user_id, None)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def is_courier(user_id: int) -> bool:
    return user_id in COURIER_IDS or is_admin(user_id)


# ==============================
# КЛИЕНТСКИЕ КОМАНДЫ
# ==============================


def handle_start(chat_id: int):
    text = (
        "Привет! Я бот доставки FastBox 🚚\n\n"
        "Я помогаю оформить доставку вещей, еды, продуктов и лекарств "
        "по городам и регионам Казахстана, а также планировать доставку заранее.\n\n"
        "Основные команды:\n"
        "/order — создать заказ\n"
        "/history — мои заказы\n"
        "/track <id> — отследить заказ\n"
        "/help — помощь\n"
        "/cancel — отменить текущий диалог\n\n"
        "Администратор: /admin\n"
        "Курьер: /courier_orders"
    )
    send_message(chat_id, text)


def handle_help(chat_id: int):
    text = (
        "❓ Помощь FastBox\n\n"
        "Клиент:\n"
        "/order — создать новый заказ\n"
        "/history — показать ваши заказы\n"
        "/track <номер> — показать статус заказа\n"
        "/cancel — отменить текущий процесс\n\n"
        "Администратор:\n"
        "/admin — показать команды администратора\n"
        "/all_orders — список всех заказов\n"
        "/set_status <id> <STATUS> — сменить статус заказа\n\n"
        "Курьер:\n"
        "/courier_orders — заказы со статусом COURIER_ASSIGNED"
    )
    send_message(chat_id, text)


def handle_cancel(chat_id: int, user_id: int):
    reset_user_state(user_id)
    send_message(chat_id, "Текущий процесс создания заказа отменён.")


def start_order(chat_id: int, user_id: int):
    reset_user_state(user_id)
    user_state[user_id] = "order_type"
    temp_order_data[user_id] = {}
    text = (
        "Начинаем создание заказа.\n\n"
        "Выберите тип доставки и напишите в чат:\n"
        "1 — Вещи\n"
        "2 — Еда\n"
        "3 — Продукты\n"
        "4 — Лекарства\n\n"
        "Либо напишите словами: Вещи, Еда, Продукты, Лекарства"
    )
    send_message(chat_id, text)


def process_order_step(chat_id: int, user_id: int, text: str):
    global order_counter

    state = user_state.get(user_id)

    if state is None:
        send_message(chat_id, "Я вас не понял. Используйте /order для создания заказа.")
        return

    data = temp_order_data.setdefault(user_id, {})

    # 1. Тип доставки
    if state == "order_type":
        t = text.strip().lower()
        mapping = {
            "1": OrderType.THINGS,
            "2": OrderType.FOOD,
            "3": OrderType.GROCERIES,
            "4": OrderType.MEDICINE,
            "вещи": OrderType.THINGS,
            "еда": OrderType.FOOD,
            "продукты": OrderType.GROCERIES,
            "лекарства": OrderType.MEDICINE,
        }
        if t not in mapping:
            send_message(chat_id, "Пожалуйста, выберите 1/2/3/4 или введите: Вещи, Еда, Продукты, Лекарства.")
            return
        data["order_type"] = mapping[t]
        user_state[user_id] = "city_from"
        send_message(chat_id, "Из какого города отправляем? (например: Костанай)")
        return

    # 2. Город отправителя
    if state == "city_from":
        data["city_from"] = text.strip()
        user_state[user_id] = "from_address"
        send_message(chat_id, "Укажите адрес отправителя (улица, дом, подъезд и т.п.):")
        return

    # 3. Адрес отправителя
    if state == "from_address":
        data["from_address"] = text.strip()
        user_state[user_id] = "city_to"
        send_message(chat_id, "В какой город доставляем? (например: Астана)")
        return

    # 4. Город получателя
    if state == "city_to":
        data["city_to"] = text.strip()
        user_state[user_id] = "to_address"
        send_message(chat_id, "Укажите адрес получателя:")
        return

    # 5. Адрес получателя
    if state == "to_address":
        data["to_address"] = text.strip()
        user_state[user_id] = "weight"
        send_message(chat_id, "Укажите вес посылки в кг (например: 1.5):")
        return

    # 6. Вес
    if state == "weight":
        t = text.replace(",", ".").strip()
        try:
            w = float(t)
            if w <= 0:
                raise ValueError
        except ValueError:
            send_message(chat_id, "Пожалуйста, введите число больше 0 (например: 0.5).")
            return
        data["weight_kg"] = w
        user_state[user_id] = "schedule_choice"
        send_message(
            chat_id,
            "Когда выполнить доставку?\n"
            "- Напишите: сейчас\n"
            "- или: позже (если хотите запланировать на дату/время)"
        )
        return

    # 7. Выбор: сейчас или позже
    if state == "schedule_choice":
        t = text.strip().lower()
        if t.startswith("сейча") or t == "сейчас":
            data["scheduled"] = False
            data["scheduled_date"] = None
            data["time_window"] = None
            user_state[user_id] = "comment"
            send_message(chat_id, "Добавьте комментарий к заказу (или напишите '-' если без комментария):")
            return
        elif t.startswith("позж") or t == "позже":
            data["scheduled"] = True
            user_state[user_id] = "date"
            send_message(chat_id, "Введите дату доставки в формате ГГГГ-ММ-ДД (например: 2025-12-10):")
            return
        else:
            send_message(chat_id, "Напишите 'сейчас' или 'позже'.")
            return

    # 8. Дата
    if state == "date":
        t = text.strip()
        try:
            datetime.strptime(t, "%Y-%m-%d")
        except ValueError:
            send_message(chat_id, "Неверный формат. Введите дату: ГГГГ-ММ-ДД (например: 2025-12-10).")
            return
        data["scheduled_date"] = t
        user_state[user_id] = "time_window"
        send_message(chat_id, "Введите интервал времени (например: 14:00-16:00):")
        return

    # 9. Интервал времени
    if state == "time_window":
        data["time_window"] = text.strip()
        user_state[user_id] = "comment"
        send_message(chat_id, "Добавьте комментарий к заказу (или '-' если без комментария):")
        return

    # 10. Комментарий
    if state == "comment":
        comment = text.strip()
        if comment == "-":
            comment = ""
        data["comment"] = comment

        # Подготовка к подтверждению
        order_type: OrderType = data["order_type"]
        city_from: str = data["city_from"]
        from_address: str = data["from_address"]
        city_to: str = data["city_to"]
        to_address: str = data["to_address"]
        weight_kg: float = data["weight_kg"]
        scheduled_date: Optional[str] = data.get("scheduled_date")
        time_window: Optional[str] = data.get("time_window")
        scheduled_flag: bool = bool(data.get("scheduled", False))

        price = calculate_price_kzt(
            weight_kg=weight_kg,
            city_from=city_from,
            city_to=city_to,
            scheduled=scheduled_flag,
        )
        data["price_kzt"] = price

        summary = (
            "Проверьте данные заказа:\n\n"
            f"Тип: {order_type.value}\n"
            f"Откуда: {city_from}, {from_address}\n"
            f"Куда: {city_to}, {to_address}\n"
            f"Вес: {weight_kg} кг\n"
            f"Дата: {scheduled_date or 'сегодня'}\n"
            f"Время: {time_window or 'как можно скорее'}\n"
            f"Комментарий: {comment or '-'}\n"
            f"Расчётная стоимость: {price} ₸\n\n"
            "Если всё верно, напишите: да\n"
            "Если хотите отменить — напишите: нет"
        )
        send_message(chat_id, summary)
        user_state[user_id] = "confirm"
        return

    # 11. Подтверждение
    if state == "confirm":
        t = text.strip().lower()
        if t.startswith("д") or t == "да":
            order_type: OrderType = data["order_type"]
            city_from: str = data["city_from"]
            from_address: str = data["from_address"]
            city_to: str = data["city_to"]
            to_address: str = data["to_address"]
            weight_kg: float = data["weight_kg"]
            comment: str = data.get("comment", "")
            scheduled_date: Optional[str] = data.get("scheduled_date")
            time_window: Optional[str] = data.get("time_window")
            price_kzt: int = data["price_kzt"]
            scheduled_flag: bool = bool(data.get("scheduled", False))

            status = OrderStatus.SCHEDULED if scheduled_flag else OrderStatus.CREATED

            order = Order(
                id=order_counter,
                user_id=user_id,
                order_type=order_type,
                city_from=city_from,
                from_address=from_address,
                city_to=city_to,
                to_address=to_address,
                weight_kg=weight_kg,
                comment=comment,
                scheduled_date=scheduled_date,
                time_window=time_window,
                price_kzt=price_kzt,
                status=status,
            )

            orders_store[order_counter] = order
            user_orders_index.setdefault(user_id, []).append(order_counter)

            send_message(chat_id, f"Заказ создан ✅\n\n{format_order(order)}")
            send_message(chat_id, "Отследить можно командой: /track " + str(order_counter))

            order_counter += 1
            reset_user_state(user_id)
            return

        elif t.startswith("н") or t == "нет":
            reset_user_state(user_id)
            send_message(chat_id, "Заказ отменён.")
            return
        else:
            send_message(chat_id, "Напишите 'да' или 'нет'.")
            return


def handle_history(chat_id: int, user_id: int):
    ids = user_orders_index.get(user_id, [])
    if not ids:
        send_message(chat_id, "У вас пока нет заказов.")
        return

    lines = ["📦 Ваши заказы:"]
    for oid in sorted(ids, reverse=True)[:10]:
        o = orders_store.get(oid)
        if not o:
            continue
        lines.append(f"• №{o.id} — {o.order_type.value}, {o.status.value}, {o.price_kzt} ₸")
    send_message(chat_id, "\n".join(lines))


def handle_track(chat_id: int, user_id: int, args: List[str]):
    if not args:
        send_message(chat_id, "Используйте: /track <номер_заказа>. Пример: /track 1")
        return
    if not args[0].isdigit():
        send_message(chat_id, "Номер заказа должен быть числом. Пример: /track 1")
        return
    oid = int(args[0])
    order = orders_store.get(oid)
    if not order:
        send_message(chat_id, "Заказ с таким номером не найден.")
        return
    if order.user_id != user_id and not is_admin(user_id):
        send_message(chat_id, "Вы не можете просматривать этот заказ.")
        return
    send_message(chat_id, format_order(order))


# ==============================
# АДМИНСКИЕ И КУРЬЕРСКИЕ КОМАНДЫ
# ==============================


def handle_admin(chat_id: int, user_id: int):
    if not is_admin(user_id):
        send_message(chat_id, "Эта команда доступна только администратору.")
        return
    text = (
        "🛠 Админ-панель FastBox\n\n"
        "/all_orders — показать все заказы\n"
        "/set_status <id> <STATUS> — сменить статус заказа\n\n"
        "Доступные статусы:\n"
        + ", ".join(s.name for s in OrderStatus)
    )
    send_message(chat_id, text)


def handle_all_orders(chat_id: int, user_id: int):
    if not is_admin(user_id):
        send_message(chat_id, "Эта команда доступна только администратору.")
        return

    if not orders_store:
        send_message(chat_id, "Заказов пока нет.")
        return

    lines = ["📦 Все заказы:"]
    for oid in sorted(orders_store.keys()):
        o = orders_store[oid]
        lines.append(
            f"• №{o.id} — {o.order_type.value}, {o.status.value}, {o.price_kzt} ₸ "
            f"(user_id={o.user_id})"
        )
    send_message(chat_id, "\n".join(lines))


def handle_set_status(chat_id: int, user_id: int, args: List[str]):
    if not is_admin(user_id):
        send_message(chat_id, "Эта команда доступна только администратору.")
        return

    if len(args) != 2:
        send_message(chat_id, "Использование: /set_status <id> <STATUS>")
        return

    if not args[0].isdigit():
        send_message(chat_id, "id заказа должен быть числом.")
        return

    oid = int(args[0])
    status_name = args[1].upper()

    order = orders_store.get(oid)
    if not order:
        send_message(chat_id, "Заказ с таким номером не найден.")
        return

    try:
        new_status = OrderStatus[status_name]
    except KeyError:
        send_message(
            chat_id,
            "Неверный статус. Доступные:\n" + ", ".join(s.name for s in OrderStatus),
        )
        return

    order.status = new_status
    send_message(chat_id, f"Статус заказа №{oid} изменён на {new_status.value}.")


def handle_courier_orders(chat_id: int, user_id: int):
    if not is_courier(user_id):
        send_message(chat_id, "Эта команда доступна только курьерам или администратору.")
        return

    # Показываем заказы в статусе COURIER_ASSIGNED
    orders = [
        o for o in orders_store.values()
        if o.status == OrderStatus.COURIER_ASSIGNED
    ]
    if not orders:
        send_message(chat_id, "Сейчас нет заказов со статусом COURIER_ASSIGNED.")
        return

    lines = ["🚴 Заказы для курьеров (COURIER_ASSIGNED):"]
    for o in orders:
        lines.append(
            f"• №{o.id} — {o.order_type.value}, {o.city_from} → {o.city_to}, {o.price_kzt} ₸"
        )
    send_message(chat_id, "\n".join(lines))


# ==============================
# ОБРАБОТКА ВХОДЯЩИХ
# ==============================


def handle_message(msg: dict):
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    text = msg.get("text")

    if not text:
        return

    # Команды
    if text.startswith("/"):
        parts = text.split()
        cmd = parts[0]
        args = parts[1:]

        if cmd == "/start":
            handle_start(chat_id)
            reset_user_state(user_id)
        elif cmd == "/help":
            handle_help(chat_id)
        elif cmd == "/order":
            start_order(chat_id, user_id)
        elif cmd == "/history":
            handle_history(chat_id, user_id)
        elif cmd == "/track":
            handle_track(chat_id, user_id, args)
        elif cmd == "/cancel":
            handle_cancel(chat_id, user_id)
        elif cmd == "/admin":
            handle_admin(chat_id, user_id)
        elif cmd == "/all_orders":
            handle_all_orders(chat_id, user_id)
        elif cmd == "/set_status":
            handle_set_status(chat_id, user_id, args)
        elif cmd == "/courier_orders":
            handle_courier_orders(chat_id, user_id)
        else:
            send_message(chat_id, "Неизвестная команда. Используйте /help.")
        return

    # Если пользователь в процессе создания заказа — обрабатываем шаг
    if user_id in user_state:
        process_order_step(chat_id, user_id, text)
    else:
        send_message(
            chat_id,
            "Я вас не понял. Используйте /order для создания заказа или /help для помощи.",
        )


# ==============================
# MAIN LOOP
# ==============================


def main():
    print("FastBox Telegram bot (простая версия) запущен.")
    last_update_id = None

    while True:
        updates = get_updates(last_update_id)
        for upd in updates:
            last_update_id = upd["update_id"] + 1

            if "message" in upd:
                try:
                    handle_message(upd["message"])
                except Exception as e:
                    print("Error in handle_message:", e)

        time.sleep(1)


if __name__ == "__main__":
    main()
