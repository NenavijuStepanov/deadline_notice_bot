import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.session.aiohttp import AiohttpSession

user_router = Router()

@user_router.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "Привет! Я бот для создания дедлайнов! Ниже приведен список команд\n\n"
        "<code>/add *ключевоеслово *время(24 формат) *дата(строго дд.мм.гггг)</code> - добавление дедлайнов, пиши ровно по образцу, иначе твоя мать сдохнет"
    )
    await message.answer(text, parse_mode="HTML")

@user_router.message(Command("add"))
async def cmd_add(message: Message):
    await message.answer("Привет! Я бот для создания дедлайнов!")

@user_router.message(Command("delete"))
async def cmd_add(message: Message):
    await message.answer("Привет! Я бот для создания дедлайнов!")

@user_router.message(Command("edit"))
async def cmd_add(message: Message):
    await message.answer("Привет! Я бот для создания дедлайнов!")

@user_router.message(Command("send_to_topic"))
async def send_to_specific_topic(message: Message, bot: Bot):
    chat_id = message.chat.id # ID твоей супергруппы
    
    # Допустим, ты узнал, что ID темы "Техподдержка" равен 15
    target_topic_id = 15 
    
    # При отправке через bot.send_message нужно ЯВНО указывать message_thread_id
    await bot.send_message(
        chat_id=chat_id,
        text="🚨 Внимание! Это системное сообщение в тему Техподдержки.",
        message_thread_id=target_topic_id
    )

@user_router.message(Command("format"))
async def send_formatted_text(message: Message):
    text = (
        "<b>Жирный текст</b>\n"
        "<strong>Тоже жирный текст</strong>\n\n"
        
        "<i>Курсив</i>\n"
        "<em>Тоже курсив</em>\n\n"
        
        "<u>Подчеркнутый</u>\n"
        "<s>Зачеркнутый</s>\n\n"
        
        "<b><i>Жирный курсив</i></b>\n\n"
        
        # Спойлер (текст скрыт, пока по нему не кликнешь)
        "<tg-spoiler>Текст под спойлером</tg-spoiler>\n\n"
        
        # Код (моноширинный шрифт, копируется в буфер по клику)
        "Строчный код: <code>import aiogram</code>\n\n"
        
        # Блок кода с подсветкой синтаксиса конкретного языка
        "Блок кода на Python:\n"
        '<pre><code class="language-python">'
        "def main():\n"
        "    print('Hello World')"
        "</code></pre>\n\n"
        
        # Ссылка, зашитая в текст
        'Ссылка на <a href="https://t.me/telegram">Официальный канал TG</a>'
    )

    await message.answer(text, parse_mode="HTML")