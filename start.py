import asyncio
import logging

from aiogram.types import FSInputFile
from aiogram.fsm.state import StatesGroup, State

from src.handlers import *

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='src/bot.log')


class CreateProfile(StatesGroup):
    name = State()
    description = State()
    city = State()
    photo = State()
    sex = State()
    age = State()
    social_link = State()


class SearchPair(StatesGroup):
    SearchStart = State()
    InActiveSearch = State()


async def show_profile(from_id, user_id):
    if db.profile_exists(user_id):
        user_data = db.get_info(user_id)
        info = (f"Имя: {user_data[2]}\n"
                f"Пол: {user_data[6]}\n"
                f"Возраст: {user_data[7]}\n"
                f"Город: {user_data[4]}\n"
                f"Описание: {user_data[3]}\n"
                f"tg: @{user_data[1]}")
        if user_data[-1] != "Скип":
            info += f"\nСсылочка: {user_data[-1]}"
        photo = FSInputFile(f"src/photos/{user_id}.jpg")
        await bot.send_photo(from_id, photo, caption=info)
    else:
        await bot.send_message(from_id, "Ты как сюда попал, у тебя профиля нет")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
