from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from src.config import get_db_connection
from ..database.queries import CHECK_USER_QUERY
from ..keyboards.builders import main_menu_keyboard, create_new_profile_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    conn = None
    try:
        conn = await get_db_connection()
        user_exists = await conn.fetchval(
            CHECK_USER_QUERY,
            message.from_user.id
        )

        if user_exists:
            await state.clear()
            keyboard = main_menu_keyboard()
            await message.answer(
                "Главное меню:",
                reply_markup=keyboard
            )
        else:
            keyboard = create_new_profile_keyboard()
            await message.answer(
                "Добро пожаловать! Для начала создайте профиль.",
                reply_markup=keyboard
            )

    except Exception as e:
        await message.answer("❌ Ошибка при загрузке профиля LOL")
        print(f"Error: {e}")

    finally:
        if conn:
            await conn.close()
