import os
import asyncio
from aiogram import Bot, Dispatcher

from src.handlers.common import router as common_router
from src.handlers.profile import router as profiles_router
from src.handlers.search import router as search_router

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

async def main():
    dgap_photo = open('dgap.jpg')
    dp.include_routers(
        common_router,
        profiles_router,
        search_router,
    )
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
