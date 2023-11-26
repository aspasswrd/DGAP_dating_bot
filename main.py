import logging

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

from handlers import *

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log')

bot = Bot(token="6988902728:AAFloEdVRQe_pptszssonORpyuWEa9Fzfew")
dp = Dispatcher(bot, storage=MemoryStorage())
BotDataBase = BotDataBase('database.db')

main_text = '1. Искать фопфика/бмочку\n2. Мой профиль\n3. Удалить профиль'
profile_text = '1. Заполнить профиль заново\n2. Изменить текст профиль\n3. Изменить фото\n4. Вернутся назад'


class AllStates(StatesGroup):
    my_profile_feedback = State()
    profile_reaction = State()
    name = State()
    age = State()
    city = State()
    text = State()
    photo = State()
    choosing_gender = State()
    choosing_interest = State()
    menu_answer = State()
    change_text = State()
    change_photo = State()
    delete_confirm = State()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
