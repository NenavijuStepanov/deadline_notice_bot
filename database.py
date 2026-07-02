import aiosqlite # Библиотека sqlite3 синхронная. Лучше использовать асинхронную aiosqlite
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

DB_NAME = os.getenv("DB_NAME")

async def init_db():
    """Создает таблицу дедлайнов, если её еще нет"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS deadlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                thread_id INTEGER,
                title TEXT,
                description TEXT,
                deadline_dt TEXT, -- Будем хранить тут дату и время вместе в формате YYYY-MM-DD HH:MM
                sent_week INTEGER DEFAULT 0,  -- Напомнили за неделю
                sent_3days INTEGER DEFAULT 0, -- Напомнили за 3 дня
                sent_day INTEGER DEFAULT 0,   -- Напомнили за день
                sent_hour INTEGER DEFAULT 0, -- Напоминание за час
                sent_final INTEGER DEFAULT 0  -- Финальный дедлайн
            )
        """)
        await db.commit()

async def add_deadline(chat_id: int, user_id: int, thread_id: int | None, title: str, time_str: str, date_str: str, description: str) -> bool:
    """Конвертирует дату/время пользователя и сохраняет дедлайн в базу"""
    try:
        db_dt_format = date_str + " " + time_str

        parsed_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        
        # Решаем капкан: проверяем, сколько времени осталось с момента создания
        now = datetime.now()
        time_left = parsed_dt - now
        
        # Если дедлайн уже ближе, чем неделя/3дня/день, автоматически глушим эти уведомления
        sent_week = 1 if time_left <= timedelta(days=7) else 0
        sent_3days = 1 if time_left <= timedelta(days=3) else 0
        sent_day = 1 if time_left <= timedelta(days=1) else 0
        sent_hour = 1 if time_left <= timedelta(hours=1) else 0

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT INTO deadlines (chat_id, user_id, thread_id, title, description, deadline_dt, sent_week, sent_3days, sent_day, sent_hour) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (chat_id, user_id, thread_id, title, description, db_dt_format, sent_week, sent_3days, sent_day, sent_hour))
            await db.commit()
        return True
    except ValueError:
        # Если пользователь ввел кривую дату (например, 14:88 или 32.13.2026)
        return False

async def get_reminders_week():
    """Ищет задачи, до которых осталось 7 дней или меньше, и уведомление еще не ушло"""
    target_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, chat_id, thread_id, title, description, deadline_dt FROM deadlines WHERE deadline_dt <= ? AND sent_week = 0", 
            (target_str,)
        ) as cursor:
            return await cursor.fetchall()

async def get_reminders_3days():
    """Ищет задачи, до которых осталось 3 дня или меньше"""
    target_str = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, chat_id, thread_id, title, description, deadline_dt FROM deadlines WHERE deadline_dt <= ? AND sent_3days = 0", 
            (target_str,)
        ) as cursor:
            return await cursor.fetchall()

async def get_reminders_day():
    """Ищет задачи, до которых остались 24 часа или меньше"""
    target_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, chat_id, thread_id, title, description, deadline_dt FROM deadlines WHERE deadline_dt <= ? AND sent_day = 0", 
            (target_str,)
        ) as cursor:
            return await cursor.fetchall()

async def get_reminders_hour():
    """Ищет задачи, до которых остался час или меньше, и уведомление еще не ушло"""
    target_str = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, chat_id, thread_id, title, description, deadline_dt FROM deadlines WHERE deadline_dt <= ? AND sent_hour = 0", 
            (target_str,)
        ) as cursor:
            return await cursor.fetchall()

async def get_final_deadlines():
    """Ищет наступившие дедлайны"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, chat_id, thread_id, title, description FROM deadlines WHERE deadline_dt <= ? AND sent_final = 0", 
            (now_str,)
        ) as cursor:
            return await cursor.fetchall()

# --- ФУНКЦИИ ОБНОВЛЕНИЯ СТАТУСА ---

async def mark_as_sent(task_id: int, column: str):
    """Универсальная функция для отметки отправленного уведомления"""
    # Здесь безопасно использовать f-строку, так как имя колонки передаем мы сами из кода, а не юзер
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f"UPDATE deadlines SET {column} = 1 WHERE id = ?", (task_id,))
        await db.commit()

async def get_deadlines(chat_id: int):
    """Возвращает список активных дедлайнов для конкретного чата по убыванию времени"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Выбираем только не отправленные (sent_final = 0) и сортируем по возрастанию
        async with db.execute(
            "SELECT id, title, deadline_dt, description FROM deadlines WHERE chat_id = ? AND sent_final = 0 ORDER BY deadline_dt",
            (chat_id,)
        ) as cursor:
            return await cursor.fetchall()
        
async def delete_deadline(deadline_id: int, chat_id: int) -> bool:
    """Безопасно удаляет дедлайн, проверяя его принадлежность к чату"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "DELETE FROM deadlines WHERE id = ? AND chat_id = ?",
            (deadline_id, chat_id)
        )
        await db.commit()
        # cursor.rowcount вернет количество удаленных строк. 
        # Если строк > 0, значит удаление прошло успешно.
        return cursor.rowcount > 0
    
async def get_archive(chat_id: int):
    """Возвращает список активных дедлайнов для конкретного чата по убыванию времени"""
    async with aiosqlite.connect(DB_NAME) as db:
        # Выбираем только не отправленные (sent_final = 0) и сортируем по убыванию (DESC)
        async with db.execute(
            "SELECT title, deadline_dt, description FROM deadlines WHERE chat_id = ? AND sent_final = 1 ORDER BY deadline_dt DESC",
            (chat_id,)
        ) as cursor:
            return await cursor.fetchall()