import asyncio
from aiogram import Dispatcher

from src.handlers.common import router as common_router
from src.handlers.profile import router as profiles_router
from src.handlers.search import router as search_router

from src.config import bot

dp = Dispatcher()

async def main():
    dp.include_routers(
        common_router,
        profiles_router,
        search_router,
    )
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
