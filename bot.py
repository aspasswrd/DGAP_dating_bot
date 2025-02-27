import os
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from dotenv import load_dotenv
import asyncpg

import src.registration

# Загрузка переменных окружения
load_dotenv('src/.env')

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

router = Router()

# Подключение к БД
async def get_db_connection():
    return await asyncpg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

class MainMenu(StatesGroup):
    main = State()
    view_profile = State()

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
            await state.clear()
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="🔍 Поиск")],
                    [types.KeyboardButton(text="👤 Мой профиль")],
                    [types.KeyboardButton(text="❌ Удалить профиль")]
                ],
                resize_keyboard=True
            )
            await message.answer(
                "Главное меню:",
                reply_markup=keyboard
            )
            await state.set_state(MainMenu.main)
        else:
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="Создать профиль")]
                ],
                resize_keyboard=True
            )
            await message.answer(
                "Добро пожаловать! Для начала создайте профиль.",
                reply_markup=keyboard
            )

    except Exception as e:
        await message.answer("❌ Ошибка при загрузке профиля")
        print(f"Error: {e}")

    finally:
        if conn:
            await conn.close()


@router.message(F.text == "Создать профиль")
async def create_profile(message: Message, state: FSMContext):
    await message.answer("Давайте создадим ваш профиль.\nВведите ваше имя:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(src.registration.Registration.get_name)


@router.message(F.text == "❌ Удалить профиль")
async def delete_profile(message: Message):
    conn = None
    try:
        conn = await get_db_connection()

        async with conn.transaction():
            # Каскадное удаление сработает благодаря REFERENCES CASCADE
            await conn.execute(
                "DELETE FROM bot.users WHERE user_id = $1",
                message.from_user.id
            )

        await message.answer(
            "Ваш профиль успешно удалён!",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await cmd_start(message, state=None)  # Показываем стартовое меню

    except Exception as e:
        await message.answer("❌ Ошибка при удалении профиля")
        print(f"Error: {e}")

    finally:
        if conn:
            await conn.close()


# Добавим обработчик просмотра профиля
@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message, state: FSMContext):
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
            await state.set_state(MainMenu.main)

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




# Запуск бота
async def main():
    dp.include_routers(router, src.registration.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
