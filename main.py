import asyncio                                             

from aiogram import Bot, Dispatcher, F    
from aiogram.types import Message       
from aiogram.filters import Command, CommandStart
from handlers.subscription import subscription_router               

dp = Dispatcher()  
token = "8942961464:AAGqr4aO2uHw8y9Bg0Kf7fE6L1dqpRynOkc"
if not token:                       
    error = "No token provided"     
    raise ValueError(error)        
bot = Bot(token=token)              
dp.include_router(subscription_router)

async def main():
    print("Starting bot...")
    try:
        await dp.start_polling(bot)      
    finally:
        await bot.session.close()
        print("Bot stopped")


if __name__ == '__main__':
    asyncio.run(main())