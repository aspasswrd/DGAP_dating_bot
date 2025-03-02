from fileinput import filename

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types.message import Message
from aiogram.filters import StateFilter
from aiogram.utils import keyboard

from .common import cmd_main_menu
from ..config import get_db_connection
from ..database.queries import *
from ..handlers.common import cmd_start
from ..keyboards.builders import inline_edit_profile_keyboard, edit_preferences_keyboard
from ..states.registration import Registration
from ..states.preferences import Preferences

from ..handlers.common import cmd_start

router = Router()

from ..config import bot, upload_image

from aiogram.types import BufferedInputFile, CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup

@router.callback_query(F.data == 'profile')
async def show_profile(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    conn = None
    try:
        conn = await get_db_connection()
        user = await conn.fetchrow(SELECT_USER_QUERY, callback.from_user.id)

        if user:
            photos = await conn.fetch(SELECT_USER_PHOTO_QUERY, callback.from_user.id)

            response = (
                f"👤 Ваш профиль:\n"
                f"Имя: {user['name']}\n"
                f"Возраст: {user['age']}\n"
                f"Пол: {'Мужчина' if user['is_male'] else 'Женщина'}\n"
                f"Поиск: {user['min_age']}-{user['max_age']} лет, "
                f"радиус {user['search_radius']} км\n"
            )

            if photos:
                media = InputMediaPhoto(
                    media=photos[0]['photo'],
                    caption=response,
                )

                await callback.message.edit_media(
                    media=media,
                    reply_markup=inline_edit_profile_keyboard
                )

                await callback.answer()
            else:
                await callback.message.answer(response)
                await conn.close()
                await callback.answer()

    except Exception as e:
        await callback.answer("❌ Ошибка при загрузке профиля")
        print(f"Error: {e}")
        await conn.close()

    finally:
        if conn:
            await conn.close()

@router.callback_query(F.data == 'delete_profile')
async def delete_profile(callback: CallbackQuery):
    await callback.answer()
    conn = None
    try:
        conn = await get_db_connection()

        async with conn.transaction():
            # Каскадное удаление сработает благодаря REFERENCES CASCADE
            await conn.execute(
                DELETE_USER_QUERY,
                callback.from_user.id
            )

        await callback.message.answer(
            "Ваш профиль успешно удалён!\nЕсли хочешь создать новый профиль напиши /start",
            reply_markup=types.ReplyKeyboardRemove(),
        )

    except Exception as e:
        await callback.message.answer("❌ Ошибка при удалении профиля")
        print(f"Error: {e}")

    finally:
        if conn:
            await conn.close()


@router.message(F.text == "Создать профиль")
async def create_profile(message: Message, state: FSMContext):
    await message.answer("Давайте создадим ваш профиль.\nВведите ваше имя:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.get_name)


@router.message(StateFilter(Registration.get_name))
async def process_name(message: Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer("Имя слишком длинное. Максимум 50 символов.")
        return

    await state.update_data(name=message.text)
    await message.answer("Введите ваш возраст (14-100 лет):")
    await state.set_state(Registration.get_age)


# Обработчик возраста
@router.message(StateFilter(Registration.get_age))
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if not 14 <= age <= 100:
            raise ValueError
    except ValueError:
        await message.answer("Некорректный возраст. Введите число от 14 до 100.")
        await process_age(message, state)
        return

    await state.update_data(age=age)

    # Создаем клавиатуру для выбора пола
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Мужчина")],
            [types.KeyboardButton(text="Женщина")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите ваш пол:", reply_markup=keyboard)
    await state.set_state(Registration.get_gender)


# Обработчик пола
@router.message(StateFilter(Registration.get_gender))
async def process_gender(message: Message, state: FSMContext):
    gender_mapping = {
        "мужчина": True,
        "женщина": False
    }

    is_male = gender_mapping.get(message.text.lower())
    if is_male is None:
        await message.answer("Пожалуйста, выберите пол из предложенных вариантов!")
        return

    await state.update_data(is_male=is_male)
    await message.answer("Отправьте вашу геолокацию:",
                         reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.get_location)


# Обработчик геолокации
@router.message(StateFilter(Registration.get_location), F.location)
async def process_location(message: Message, state: FSMContext):
    location = message.location
    await state.update_data(
        longitude=location.longitude,
        latitude=location.latitude
    )
    await message.answer("Теперь отправьте ваше фото профиля:")
    await state.set_state(Registration.get_photo)


# Обработчик фото
@router.message(StateFilter(Registration.get_photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    await message.answer("Я использую бесплатный хост фоток, так что придется подождать(")
    photo = message.photo[-1]

    # Скачиваем фото в бинарном виде
    photo_file = await bot.get_file(photo.file_id)
    photo_bytes = await bot.download_file(photo_file.file_path)

    image_url = await upload_image(photo_bytes)

    if image_url:
        await message.answer(f"Фото успешно загружено!")
    else:
        await message.answer("Не удалось загрузить фото.\nImgur говно.")

    # Получаем все данные
    data = await state.get_data()

    try:
        conn = await get_db_connection()

        async with conn.transaction():
            # Сохраняем пользователя
            await conn.execute(INSERT_USER_QUERY,
                               message.from_user.id,
                               message.from_user.username,
                               data["name"],
                               data["is_male"],
                               data["age"],
                               f"POINT({data['longitude']} {data['latitude']})")

            # Сохраняем фото
            await conn.execute(INSERT_USER_PHOTO_QUERY,
                               message.from_user.id,
                               image_url)

            # Устанавливаем дефолтные предпочтения
            await conn.execute(INSERT_USER_PREFERENCES_QUERY,
                               message.from_user.id,
                               data["age"] - 2 if data["age"] > 16 else 14,
                               data["age"] + 2,
                               10)

        await message.answer(
            "✅ Профиль успешно создан!\n"
            f"Имя: {data['name']}\n"
            f"Возраст: {data['age']}\n"
            f"Пол: {'Мужчина' if data['is_male'] else 'Женщина'}"
        )
        await state.clear()
        await cmd_start(message, state)

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении профиля. Попробуйте позже.")
        print(f"Database error: {e}")

    finally:
        if conn:
            await conn.close()
        await state.clear()


@router.callback_query(F.data == "edit_preferences")
async def edit_preferences(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Preferences.get_min_age)  # Сразу переходим к первому шагу
    await callback.message.answer("Введите минимальный возраст партнера (не менее 14):")


@router.message(StateFilter(Preferences.get_min_age))
async def process_min_age(message: Message, state: FSMContext):
    try:
        min_age = int(message.text)
        if not 14 <= min_age <= 100:
            raise ValueError
        await state.update_data(min_age=min_age)
        await message.answer("Теперь введите максимальный возраст (до 100 лет):")
        await state.set_state(Preferences.get_max_age)
    except ValueError:
        await message.answer("❌ Некорректный возраст. Введите число от 14 до 100.")


@router.message(StateFilter(Preferences.get_max_age))
async def process_max_age(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        max_age = int(message.text)
        if max_age < data["min_age"] or max_age > 100:
            raise ValueError
        await state.update_data(max_age=max_age)
        await message.answer("Теперь введите радиус поиска (в километрах):")
        await state.set_state(Preferences.get_radius)
    except ValueError:
        await message.answer(f"❌ Некорректный возраст. Введите число от {data['min_age']} до 100.")


@router.message(StateFilter(Preferences.get_radius))
async def process_radius(message: Message, state: FSMContext):
    try:
        radius = int(message.text)
        radius = min(radius, 20000)

        data = await state.get_data()
        conn = await get_db_connection()

        async with conn.transaction():
            await conn.execute(
                UPDATE_USER_PREFERENCES_QUERY,
                message.from_user.id,
                data["min_age"],
                data["max_age"],
                radius
            )

        await message.answer("✅ Настройки поиска успешно обновлены!")
        await cmd_start(message, state)

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении настроек")
        print(f"Error: {e}")
    finally:
        await state.clear()
        if conn:
            await conn.close()