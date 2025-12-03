import aiosqlite
import logging

DB_NAME = "fastbox.db"

class Database:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    async def init(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    phone TEXT,
                    is_courier BOOLEAN DEFAULT 0,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    courier_id INTEGER,
                    type TEXT,
                    city TEXT,
                    sender_address TEXT,
                    receiver_address TEXT,
                    receiver_phone TEXT,
                    comment TEXT,
                    weight TEXT,
                    delivery_date TEXT,
                    delivery_time TEXT,
                    price REAL,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(courier_id) REFERENCES users(id)
                )
            """)
            await db.commit()

    async def add_user(self, user_id, username, full_name, phone=None, is_courier=False, is_admin=False):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
                exists = await cursor.fetchone()
            
            if exists:
                if phone:
                    await db.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, user_id))
                if is_courier:
                    await db.execute("UPDATE users SET is_courier = 1 WHERE id = ?", (user_id,))
                if is_admin:
                    await db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
            else:
                await db.execute("""
                    INSERT INTO users (id, username, full_name, phone, is_courier, is_admin)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, username, full_name, phone, is_courier, is_admin))
            await db.commit()

    async def add_order(self, user_id, order_data):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("""
                INSERT INTO orders (user_id, type, city, sender_address, receiver_address, receiver_phone, comment, weight, delivery_date, delivery_time, price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, order_data['type'], order_data['city'], order_data['sender_address'], 
                  order_data['receiver_address'], order_data.get('receiver_phone'), order_data.get('comment'), 
                  order_data['weight'], order_data.get('delivery_date'), order_data.get('delivery_time'),
                  order_data.get('price'), 'created'))
            await db.commit()
            return cursor.lastrowid

    async def get_orders(self, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_all_orders(self):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM orders") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def assign_courier(self, order_id, courier_id):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE orders SET courier_id = ?, status = 'assigned' WHERE id = ?", (courier_id, order_id))
            await db.commit()

    async def get_courier_orders(self, courier_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM orders WHERE courier_id = ?", (courier_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_order_status(self, order_id, status):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
            await db.commit()
            
    async def get_order(self, order_id):
         async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
