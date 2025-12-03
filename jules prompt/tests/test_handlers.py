import pytest
import aiosqlite
import os
from unittest.mock import AsyncMock, MagicMock, patch
from src.database import Database
# We need to import the modules to patch, not just functions, to patch 'db' in them
import src.handlers.admin as admin_module
import src.handlers.courier as courier_module

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

@pytest.fixture
def mock_update_context():
    update = AsyncMock()
    context = AsyncMock()
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.effective_user.full_name = "Test User"
    return update, context

@pytest.mark.asyncio
async def test_admin_auth_failure(db, mock_update_context):
    update, context = mock_update_context
    update.effective_user.id = 999
    
    # Patch the db in the admin module to use our test db
    with patch.object(admin_module, 'db', db):
        with patch("src.handlers.admin.ADMIN_IDS", [888]):
            await admin_module.admin_orders(update, context)
            update.message.reply_text.assert_called_with("У вас нет прав администратора.")

@pytest.mark.asyncio
async def test_admin_auth_success(db, mock_update_context):
    update, context = mock_update_context
    update.effective_user.id = 888
    
    with patch.object(admin_module, 'db', db):
        with patch("src.handlers.admin.ADMIN_IDS", [888]):
            await admin_module.admin_orders(update, context)
            update.message.reply_text.assert_called_with("Нет активных заказов.")

@pytest.mark.asyncio
async def test_courier_notification(db, mock_update_context):
    update, context = mock_update_context
    update.effective_user.id = 888 # Admin
    context.args = ["1", "2"] # order 1, courier 2
    
    # Setup DB
    await db.add_user(1, "client", "Client")
    await db.add_user(2, "courier", "Courier")
    await db.add_order(1, {'type': 't', 'city': 'c', 'sender_address': 's', 'receiver_address': 'r', 'weight': 'w', 'price': 100})
    
    with patch.object(admin_module, 'db', db):
        with patch("src.handlers.admin.ADMIN_IDS", [888]):
            await admin_module.assign_courier(update, context)
        
    context.bot.send_message.assert_called()
    # Check that it messaged courier (id 2)
    # The assert might need to be more specific if multiple calls happen, but here only one is expected
    assert context.bot.send_message.call_args[1]['chat_id'] == 2

@pytest.mark.asyncio
async def test_user_notification(db, mock_update_context):
    update, context = mock_update_context
    update.effective_user.id = 2 # Courier
    context.args = ["1", "delivered"]
    
    # Setup DB
    await db.add_user(1, "client", "Client")
    await db.add_user(2, "courier", "Courier")
    order_id = await db.add_order(1, {'type': 't', 'city': 'c', 'sender_address': 's', 'receiver_address': 'r', 'weight': 'w', 'price': 100})
    await db.assign_courier(order_id, 2)
    
    with patch.object(courier_module, 'db', db):
        await courier_module.set_status(update, context)
    
    context.bot.send_message.assert_called()
    assert context.bot.send_message.call_args[1]['chat_id'] == 1
