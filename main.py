import asyncio                                             

from aiogram import Bot, Dispatcher, F    
from aiogram.types import Message       
from aiogram.filters import Command, CommandStart
from handlers.user import user_router               

dp = Dispatcher()  
token = "8749159299:AAEmBLPn-UyiUPUGJwJ79S4ZTvgYj1C5P44"
if not token:                       
    error = "No token provided"     
    raise ValueError(error)        
bot = Bot(token=token)              
dp.include_router(user_router)

async def main():
    print("Starting bot...")
    try:
        await dp.start_polling(bot)      
    finally:
        await bot.session.close()
        print("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())