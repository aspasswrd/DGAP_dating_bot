from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram import F
import asyncpg

from bot import get_db_connection, bot, MainMenu

router = Router()

class Registration(StatesGroup):
    get_name = State()
    get_age = State()
    get_gender = State()
    get_location = State()
    get_photo = State()

# Обработчик имени
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
    # Берем последнюю (наибольшего размера) версию фото
    photo = message.photo[-1]

    # Скачиваем фото в бинарном виде
    photo_file = await bot.get_file(photo.file_id)
    photo_bytes = await bot.download_file(photo_file.file_path)

    photo_data = photo_bytes.getvalue()

    # Получаем все данные
    data = await state.get_data()

    try:
        conn = await get_db_connection()

        # Начинаем транзакцию
        async with conn.transaction():
            # Сохраняем пользователя
            await conn.execute('''
                INSERT INTO bot.users(user_id, name, is_male, age, location)
                VALUES($1, $2, $3, $4, ST_GeogFromText($5))
            ''',
                               message.from_user.id,
                               data["name"],
                               data["is_male"],
                               data["age"],
                               f"POINT({data['longitude']} {data['latitude']})")

            # Сохраняем фото
            await conn.execute('''
                INSERT INTO bot.photos(user_id, photo)
                VALUES($1, $2)
            ''',
                               message.from_user.id,
                               photo_data)  # Передаем photo_data, который является типом bytes

            # Устанавливаем дефолтные предпочтения
            await conn.execute('''
                INSERT INTO bot.preferences(user_id, min_age, max_age, search_radius)
                VALUES($1, $2, $3, $4)
            ''',
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
        await state.set_state(MainMenu.main)

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении профиля. Попробуйте позже.")
        print(f"Database error: {e}")
        await state.set_state(MainMenu.main)

    finally:
        if conn:
            await conn.close()
        await state.clear()


# Добавим новые состояния


# Добавим обработку лайков
@router.callback_query(F.data.startswith("like_") | F.data.startswith("dislike_"))
async def handle_like(callback: types.CallbackQuery):
    action, target_id = callback.data.split("_")
    conn = None
    try:
        conn = await get_db_connection()
        if action == "like":
            await conn.execute(
                "INSERT INTO bot.likes(from_user, to_user) VALUES($1, $2)",
                callback.from_user.id,
                int(target_id)
            )
            await callback.answer("❤️ Вы понравились пользователю!")
        else:
            await callback.answer("👎 Вы пропустили анкету")

    except asyncpg.exceptions.UniqueViolationError:
        await callback.answer("Вы уже лайкали этого пользователя")
    except Exception as e:
        await callback.answer("❌ Ошибка обработки")
        print(f"Error: {e}")
    finally:
        if conn:
            await conn.close()
