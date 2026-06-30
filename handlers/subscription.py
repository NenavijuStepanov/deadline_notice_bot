import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.session.aiohttp import AiohttpSession

CHANNEL_ID = -1003769318540
CHANNEL_URL = "https://t.me/testoproject"

subscription_router = Router()

async def is_subscribed(bot: Bot, user_id: int, chat_id: int | str) -> bool:
    """
    Проверяет, подписан ли пользователь на чат/канал.
    Возвращает True, если подписан, и False во всех остальных случаях.
    """
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        
        # Разрешенные статусы, при которых пользователь считается участником
        # "member" — обычный участник, "administrator" — админ, "creator" — владелец
        if member.status in ["member", "administrator", "creator"]:
            return True
            
        return False
        
    except TelegramBadRequest:
        # Срабатывает, если бота нет в канале, канал удален или ID указан неверно
        print(f"Ошибка: Бот не имеет доступа к каналу/чату {chat_id}!")
        return False


### 2. ХЭНДЛЕРЫ И ЛОГИКА ВЗАИМОДЕЙСТВИЯ ###

@subscription_router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    
    # Вызываем нашу функцию проверки
    if await is_subscribed(bot, user_id, CHANNEL_ID):
        await message.answer("Привет! Ты уже подписан на наш канал, держи полный доступ!")
    else:
        # Если не подписан — генерируем кнопку со ссылкой на канал и кнопку проверки
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Подписаться на канал", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
        ])
        
        await message.answer(
            "Для использования бота, пожалуйста, подпишись на наш официальный канал:",
            reply_markup=markup
        )


# Обработчик нажатия на кнопку "Я подписался"
@subscription_router.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: Message, bot: Bot):
    user_id = callback.from_user.id
    
    if await is_subscribed(bot, user_id, CHANNEL_ID):
        # Удаляем старое сообщение с кнопками подписки и пишем приветствие
        await callback.message.delete()
        await callback.message.answer("Спасибо за подписку! Бот теперь полностью доступен.")
    else:
        # Всплывающее уведомление сверху экрана, что подписка не найдена
        await callback.answer(
            text="❌ Ты всё еще не подписался! Пожалуйста, сделай это.", 
            show_alert=True
        )


@subscription_router.message()                            
async def any_message(message: Message):
    await message.answer("Я ебал твою мать!") 