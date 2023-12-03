import logging

import aiogram.types
from aiogram import types
from aiogram.types import KeyboardButton

import asyncio
from aiogram import Bot, Dispatcher, F

from database import dbworker

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log')

bot = Bot(token="6988902728:AAFloEdVRQe_pptszssonORpyuWEa9Fzfew")
dp = Dispatcher()

db = dbworker('database.db')


class CreateProfile(StatesGroup):
    name = State()
    description = State()
    city = State()
    photo = State()
    sex = State()
    age = State()
    social_link = State()


@dp.message(Command("start"))
async def start(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="/Начать"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Взлетаем брат",
        one_time_keyboard=True
    )
    await message.answer("Салам брат", reply_markup=keyboard)
    await message.answer("Нажми на кнопку начать")
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.username, message.from_user.id, message.from_user.full_name)


@dp.message(Command("Начать"))
async def magic_start(message: types.Message):
    kb_exists = [
        [
            KeyboardButton(text='/Найти парочку🔍'),
            KeyboardButton(text='/Редактировать анкету📝'),
            KeyboardButton(text='/Удалить🗑'),
        ],
    ]

    kb_not_exists = [
        [
            KeyboardButton(text='/Создать_анкету'),
        ],
    ]

    if not db.profile_exists(message.from_user.id):
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb_not_exists,
            resize_keyboard=True,
            input_field_placeholder="ЖМИ",
            one_time_keyboard=True
        )
    else:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb_exists,
            resize_keyboard=True,
            input_field_placeholder="ЖМИ",
            one_time_keyboard=True
        )

    await message.answer(
        "Выбирай че хочешь сделать",
        reply_markup=keyboard)


@dp.message(Command("Создать_анкету"))
async def create_profile(message: types.Message, state: FSMContext):
    if not db.profile_exists(message.from_user.id):
        await message.answer("Для того что бы создать твою so style анкету нужно заполнить несколько пунктов\nДавайте начнём с твоего имя, как мне тебя называть?😉")
        await state.set_state(CreateProfile.name)
    else:
        await message.answer('У тебя уже есть активная анкета\n\n')


@dp.message(CreateProfile.name)
async def get_profile_name(message: types.Message, state: FSMContext):
    kb = [
        [
            KeyboardButton(text="М"),
            KeyboardButton(text="Ж")
        ],
    ]

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="ЖМИ",
        one_time_keyboard=True
    )

    if len(str(message.text)) < 35:
        await state.update_data(profile_name=message.text.lower())
        await message.reply(
            message.text.title() + ' - четкое имя😉\nТеперь укажи какого ты пола', reply_markup=keyboard)
        await state.set_state(CreateProfile.sex)
    else:
        await message.answer("Слишком длинное имя")
        return


@dp.message(CreateProfile.sex)
async def get_profile_sex(message: types.Message, state: FSMContext):
    await state.update_data(profile_sex=message.text)
    await message.answer("Теперь напиши сколько тебе лет")
    await state.set_state(CreateProfile.age)


@dp.message(CreateProfile.age)
async def get_profile_age(message: types.Message, state: FSMContext):
    await state.update_data(profile_age=int(message.text))
    await message.reply(
        message.text + ' - да ты в самом расцвете сил\nТеперь придумай описание своего профиля')
    await state.set_state(CreateProfile.description)


@dp.message(CreateProfile.description)
async def get_profile_description(message: types.Message, state: FSMContext):
    await state.update_data(profile_description=message.text)
    await message.reply("Четко!\nУкажи из какого ты города")
    await state.set_state(CreateProfile.city)


@dp.message(CreateProfile.city)
async def get_profile_city(message: types.Message, state: FSMContext):
    await state.update_data(profile_city=message.text)
    await message.reply("Скинь свою фотку")
    await state.set_state(CreateProfile.photo)


@dp.message(CreateProfile.photo)
async def get_profile_photo(message: types.Message, state: FSMContext):
    if message.photo:
        await bot.download(
            message.photo[-1],
            destination=f"photos/{message.from_user.id}.jpg"
        )
        await message.reply("А ты сосочка)))\nТеперь кинь мне ссылку на свой вк")
        await state.set_state(CreateProfile.social_link)
    else:
        await message.answer("Надо все-таки фотку")


@dp.message(CreateProfile.social_link)
async def get_profile_link(message: types.Message, state: FSMContext):
    await state.update_data(profile_link=message.text)
    await message.answer("Теперь все совсем круто, твой профиль полностью заполнен")
    user_data = await state.get_data()
    db.create_profile(message.from_user.id, message.from_user.username, str(user_data['profile_name']),
                      str(user_data['profile_description']), str(user_data['profile_city']),
                      'photo/' + str(message.from_user.id) + '.jpg', str(user_data['profile_sex']),
                      str(user_data['profile_age']), str(user_data['profile_link']))
    await state.set_state(None)
    await magic_start(message)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
