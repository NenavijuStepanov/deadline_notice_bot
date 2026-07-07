import asyncio                                             
from aiogram import Bot, Dispatcher, F    
from aiogram.types import Message       
from aiogram.filters import Command, CommandStart
from user import user_router 
from database import mark_as_sent, init_db, get_reminders_week, get_reminders_3days, get_reminders_day, get_reminders_hour, get_final_deadlines
import os
from dotenv import load_dotenv       

async def deadline_scheduler(bot: Bot):
    
    while True:
        try:
           # 1. ПРОВЕРКА: Осталась неделя
            for task in await get_reminders_week():
                task_id, chat_id, thread_id, title, desc, dt = task
                text = f"⏳ **Внимание!** До дедлайна по задаче *'{title}'* осталась **1 неделя**!\n📅 Дата: {dt}\n📝 {desc}"
                await bot.send_message(chat_id, text, message_thread_id=thread_id, parse_mode="Markdown")
                await mark_as_sent(task_id, "sent_week")

            # 2. ПРОВЕРКА: Осталось 3 дня
            for task in await get_reminders_3days():
                task_id, chat_id, thread_id, title, desc, dt = task
                text = f"🔔 **Напоминание!** До дедлайна *'{title}'* осталось **3 дня**!\n📅 Дата: {dt}\n📝 {desc}"
                await bot.send_message(chat_id, text, message_thread_id=thread_id, parse_mode="Markdown")
                await mark_as_sent(task_id, "sent_3days")

            # 3. ПРОВЕРКА: Остался 1 день
            for task in await get_reminders_day():
                task_id, chat_id, thread_id, title, desc, dt = task
                text = f"🔥 **СРОЧНО!** До дедлайна *'{title}'* остался всего **1 день**!\n📅 Срок: {dt}\n📝 {desc}"
                await bot.send_message(chat_id, text, message_thread_id=thread_id, parse_mode="Markdown")
                await mark_as_sent(task_id, "sent_day")

            # 4. ПРОВЕРКА: Остался 1 час
            for task in await get_reminders_hour():
                task_id, chat_id, thread_id, title, desc, dt = task
                text = f"🔥 **СРОЧНО!** До дедлайна *'{title}'* остался всего **1 час**!\n📅 Срок: {dt}\n📝 {desc}"
                await bot.send_message(chat_id, text, message_thread_id=thread_id, parse_mode="Markdown")
                await mark_as_sent(task_id, "sent_hour")

            # 5. ПРОВЕРКА: Время вышло (Финальный дедлайн)
            for task in await get_final_deadlines():
                task_id, chat_id, thread_id, title, desc = task
                text = f"🚨🚨🚨 **ВРЕМЯ ВЫШЛО!** Наступил финальный дедлайн по задаче: *{title}*!\n📝 Описание: {desc}"
                await bot.send_message(chat_id, text, message_thread_id=thread_id, parse_mode="Markdown")
                await mark_as_sent(task_id, "sent_final")
                
        except Exception as e:
            print(f"Ошибка в планировщике: {e}")
            
        # cпим 60 секунд перед следующей проверкой базы
        await asyncio.sleep(60)


dp = Dispatcher()  

load_dotenv()
token = os.getenv("BOT_TOKEN")
if not token:                       
    error = "No token provided"     
    raise ValueError(error)  
      
bot = Bot(token=token)
dp.include_router(user_router)

background_tasks = set()  # создание глобального множество для защиты задания

async def main():
    print("Starting bot...")
    try:
        await init_db()

        scheduler_task = asyncio.create_task(deadline_scheduler(bot))   # запись задания в переменную
        background_tasks.add(scheduler_task)                            # добавление задания в глобальное множество для защиты от мусорщика питона
        scheduler_task.add_done_callback(background_tasks.discard)      # при ошибке или завершении работы бота, чтоб было удаление из глобального множества

        await dp.start_polling(bot)

    finally:
        await bot.session.close()
        print("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())