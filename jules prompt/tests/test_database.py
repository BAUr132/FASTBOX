import pytest
import aiosqlite
import os
from src.database import Database

DB_TEST_NAME = "test_fastbox.db"

@pytest.fixture
async def db():
    if os.path.exists(DB_TEST_NAME):
        os.remove(DB_TEST_NAME)
    
    database = Database(DB_TEST_NAME)
    await database.init()
    yield database
    
    if os.path.exists(DB_TEST_NAME):
        os.remove(DB_TEST_NAME)

@pytest.mark.asyncio
async def test_init_db(db):
    async with aiosqlite.connect(DB_TEST_NAME) as conn:
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = await cursor.fetchall()
        table_names = [t[0] for t in tables]
        assert "users" in table_names
        assert "orders" in table_names

@pytest.mark.asyncio
async def test_add_user(db):
    await db.add_user(12345, "testuser", "Test User", "+1234567890", is_courier=True)
    async with aiosqlite.connect(DB_TEST_NAME) as conn:
        async with conn.execute("SELECT * FROM users WHERE id=12345") as cursor:
            user = await cursor.fetchone()
            assert user is not None
            assert user[1] == "testuser"
            assert user[4] == 1 # is_courier

@pytest.mark.asyncio
async def test_assign_courier(db):
    await db.add_user(1, "client", "Client")
    await db.add_user(2, "courier", "Courier", is_courier=True)
    
    order_data = {
        'type': 'Вещи', 'city': 'Алматы', 'sender_address': 'A', 'receiver_address': 'B',
        'weight': 'Small', 'price': 1000
    }
    order_id = await db.add_order(1, order_data)
    
    await db.assign_courier(order_id, 2)
    
    order = await db.get_order(order_id)
    assert order['courier_id'] == 2
    assert order['status'] == 'assigned'
    
    courier_orders = await db.get_courier_orders(2)
    assert len(courier_orders) == 1

@pytest.mark.asyncio
async def test_update_status(db):
    await db.add_user(1, "client", "Client")
    order_data = {
        'type': 'Вещи', 'city': 'Алматы', 'sender_address': 'A', 'receiver_address': 'B',
        'weight': 'Small', 'price': 1000
    }
    order_id = await db.add_order(1, order_data)
    
    await db.update_order_status(order_id, "delivered")
    order = await db.get_order(order_id)
    assert order['status'] == "delivered"
