import os
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram import F
from dotenv import load_dotenv
import asyncpg

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
router = Router()


# Состояния регистрации
class Registration(StatesGroup):
    get_name = State()
    get_age = State()
    get_gender = State()
    get_location = State()
    get_photo = State()


# Подключение к БД
async def get_db_connection():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )



# Модифицируем обработчик /start
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    conn = None
    try:
        conn = await get_db_connection()
        user_exists = await conn.fetchval(
            "SELECT 1 FROM bot.users WHERE user_id = $1",
            message.from_user.id
        )

        if user_exists:
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="🔍 Поиск")],
                    [types.KeyboardButton(text="👤 Мой профиль")]
                ],
                resize_keyboard=True
            )
            await message.answer(
                "Главное меню:",
                reply_markup=keyboard
            )
            await state.set_state(MainMenu.main)
        else:
            await message.answer("Добро пожаловать! Давайте создадим ваш профиль.\nВведите ваше имя:")
            await state.set_state(Registration.get_name)

    except Exception as e:
        await message.answer("❌ Ошибка при загрузке профиля")
        print(f"Error: {e}")

    finally:
        if conn:
            await conn.close()


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

    except Exception as e:
        await message.answer("❌ Ошибка при сохранении профиля. Попробуйте позже.")
        print(f"Database error: {e}")

    finally:
        if conn:
            await conn.close()
        await state.clear()


# Добавим новые состояния
class MainMenu(StatesGroup):
    main = State()
    view_profile = State()



# Добавим обработчик просмотра профиля
@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    conn = None
    try:
        conn = await get_db_connection()
        user = await conn.fetchrow(
            "SELECT u.*, p.min_age, p.max_age, p.search_radius "
            "FROM bot.users u "
            "JOIN bot.preferences p ON u.user_id = p.user_id "
            "WHERE u.user_id = $1",
            message.from_user.id
        )

        if user:
            photos = await conn.fetch(
                "SELECT photo_id FROM bot.photos WHERE user_id = $1",
                message.from_user.id
            )

            response = (
                f"👤 Ваш профиль:\n"
                f"Имя: {user['name']}\n"
                f"Возраст: {user['age']}\n"
                f"Пол: {'Мужчина' if user['is_male'] else 'Женщина'}\n"
                f"Поиск: {user['min_age']}-{user['max_age']} лет, "
                f"радиус {user['search_radius']} км\n"
                f"Фотографий: {len(photos)}"
            )
            await message.answer(response)

    except Exception as e:
        await message.answer("❌ Ошибка при загрузке профиля")
        print(f"Error: {e}")

    finally:
        if conn:
            await conn.close()


# Добавим базовый поиск
@router.message(F.text == "🔍 Поиск")
async def start_search(message: Message, state: FSMContext):
    conn = None
    try:
        conn = await get_db_connection()
        # Получаем первого подходящего пользователя
        target = await conn.fetchrow(
            "SELECT u.* "
            "FROM bot.users u "
            "JOIN bot.preferences p ON u.user_id = p.user_id "
            "WHERE u.user_id != $1 "
            "AND u.age BETWEEN (SELECT min_age FROM bot.preferences WHERE user_id = $1) "
            "AND (SELECT max_age FROM bot.preferences WHERE user_id = $1) "
            "ORDER BY RANDOM() "
            "LIMIT 1",
            message.from_user.id
        )

        if target:
            photo = await conn.fetchrow(
                "SELECT photo FROM bot.photos WHERE user_id = $1 LIMIT 1",
                target['user_id']
            )

            caption = (
                f"👤 {target['name']}, {target['age']}\n"
                f"Пол: {'Мужчина' if target['is_male'] else 'Женщина'}"
            )

            if photo:
                await message.answer_photo(
                    photo['photo'],
                    caption=caption,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="❤️", callback_data=f"like_{target['user_id']}"),
                         types.InlineKeyboardButton(text="👎", callback_data=f"dislike_{target['user_id']}")]
                    ])
                )
            else:
                await message.answer(
                    caption,
                    reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="❤️", callback_data=f"like_{target['user_id']}"),
                         types.InlineKeyboardButton(text="👎", callback_data=f"dislike_{target['user_id']}")]
                    ])
                )

            await state.set_state(MainMenu.view_profile)
        else:
            await message.answer("😞 Пока нет подходящих анкет. Попробуйте позже!")

    except Exception as e:
        await message.answer("❌ Ошибка при поиске")
        print(f"Error: {e}")

    finally:
        if conn:
            await conn.close()


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



# Запуск бота
async def main():
    dp.include_routers(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
