import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.session.aiohttp import AiohttpSession
from database import add_deadline, get_deadlines, delete_deadline, get_archive
from datetime import datetime

user_router = Router()

async def is_admin(bot: Bot, user_id: int, channel_id: int | str) -> bool:  # -> bool чисто для редакторов, чтоб они ругались, если что-то другое будет возвращено

    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)   # нет понятия channel, есть только chat!!!
        
        # разрешенные статусы, при которых пользователь считается участником
        # "member" — обычный участник, "administrator" — админ, "creator" — владелец
        if member.status in ["administrator", "creator"]:
            return True
            
        return False
        
    except TelegramBadRequest:
        # срабатывает, если бота нет в канале, канал удален или ID указан неверно
        print(f"Ошибка: Бот не имеет доступа к каналу/чату {channel_id}!")
        return False

@user_router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if await is_admin(bot, user_id, chat_id):
        text = (
            "Привет! Я бот для создания дедлайнов! Ниже приведен список команд\n\n"
            "<code>/add Название / ЧЧ:ММ / ГГГГ-ММ-ДД / Описание</code> - добавление дедлайнов\n"
            "<code>/list</code> - список активных дедлайнов(+ кнопки удаления)\n"
            "<code>/archive</code> - список истекших дедлайнов\n"
        )
        await message.answer(text, parse_mode="HTML")
    else:
        await message.answer("Командой может воспользоваться только модератор")

@user_router.message(Command("add"))
async def cmd_add(message: Message, bot: Bot, command: CommandObject):
    user_id = message.from_user.id
    chat_id = message.chat.id
    thread_id = message.message_thread_id
    # проверяем админа
    if not await is_admin(bot, user_id, chat_id):
        await message.answer("Командой может воспользоваться только модератор")
        return

    # command.args содержит ВСЁ, что идет ПОСЛЕ команды /add (уже без самой команды и лишних пробелов)
    if not command.args:
        await message.answer("❌ Формат: /add Название / Время / Дата / Описание")
        return

    # разбиваем по слэшу и сразу очищаем элементы от случайных пробелов по краям
    user_text = [item.strip() for item in command.args.split("/")]

    # проверяем, что пользователь передал ровно 4 блока данных через слэш
    if len(user_text) < 4:
        await message.answer("❌ Не хватает данных! Проверь наличие всех 3 слэшей `/`")
        return

    title, time_str, date_str, description = user_text[0], user_text[1], user_text[2], user_text[3]

    # пытаемся сохранить в базу данных
    try:
        success = await add_deadline(chat_id, user_id, thread_id, title, time_str, date_str, description)
    
        if success:
            await message.answer(f"✅ Напоминание '{title}' успешно добавлено на {date_str} в {time_str}!")
        else:
            await message.answer("❌ Ошибка! Проверь формат даты (ГГГГ-ММ-ДД) и времени (ЧЧ:ММ).")
    except Exception as error:
        print(f"Критическая ошибка при добавлении дедлайна: {error}")
        await message.answer("⚠️ Произошла внутренняя ошибка сервера. Попробуйте позже или обратитесь к разработчику.")

@user_router.message(Command("list"))
async def cmd_list(message: Message):
    chat_id = message.chat.id

    try:
        deadlines = await get_deadlines(chat_id)
        
        if not deadlines:
            await message.answer("🎉 Активных дедлайнов пока нет!")
            return

        response = "📌 **Список активных дедлайнов:**\n\n"
        
        # Создаем список для будущих кнопок удаления
        keyboard_buttons = []
        
        # Теперь получаем еще и task_id из базы
        for task_id, title, deadline_dt, description in deadlines:
            response += f"📅 **{deadline_dt}** - *{title}*\n📝 {description}\n\n"
            
            # Для каждого дедлайна создаем кнопку. В callback_data зашиваем его id
            keyboard_buttons.append([
                InlineKeyboardButton(text=f"❌ Удалить: {title}", callback_data=f"del_{task_id}")
            ])
            
        # Формируем клавиатуру
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await message.answer(
            response, 
            parse_mode="Markdown", 
            reply_markup=reply_markup, 
        )

    except Exception as error:
        print(f"Ошибка при выводе списка дедлайнов: {error}")
        await message.answer("⚠️ Не удалось загрузить список дедлайнов.")


# ХЭНДЛЕР ДЛЯ ОБРАБОТКИ НАЖАТИЯ НА КНОПКУ УДАЛЕНИЯ
@user_router.callback_query(F.data.startswith("del_"))
async def process_delete_deadline(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    # Защита: удалять дедлайны могут только модераторы/админы
    if not await is_admin(bot, user_id, chat_id):
        await callback.answer("У вас нет прав на удаление дедлайнов!", show_alert=True)
        return

    # Вытаскиваем id дедлайна из callback_data (например из "del_5" достаем 5)
    deadline_id = int(callback.data.split("_")[1])

    # Вызываем нашу безопасную функцию удаления
    success = await delete_deadline(deadline_id, chat_id)
    
    if success:
        await callback.answer("Дедлайн успешно удален!")
        # Чтобы чат не засорялся старыми кнопками, отредактируем сообщение
        await callback.message.edit_text("🗑️ Дедлайн был удален модератором. Обновите список через /list.")
    else:
        await callback.answer("Ошибка: дедлайн не найден или уже удален.", show_alert=True)

@user_router.message(Command("archive"))
async def cmd_archive(message: Message):
    chat_id = message.chat.id
    try:
        # Получаем данные из базы
        deadlines = await get_archive(chat_id)
        
        if not deadlines:
            await message.answer("👻 Архив пустой!")
            return

        response = "📌 **Список истекших дедлайнов:**\n\n"
        
        for title, deadline_dt, description in deadlines:

            response += f"📅 **{deadline_dt}** - *{title}*\n📝 {description}\n\n"
            
        await message.answer(response, parse_mode="Markdown")

    except Exception as error:
        print(f"Ошибка при выводе архива: {error}")
        await message.answer("⚠️ Не удалось загрузить архив.")

