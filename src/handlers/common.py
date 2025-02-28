from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, BufferedInputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from src.config import get_db_connection
from ..database.queries import CHECK_USER_QUERY
from ..keyboards.builders import main_menu_keyboard, create_new_profile_keyboard, inline_main_menu_keyboard

router = Router()

dgap_photo = FSInputFile("dgap.jpg")

@router.message(Command("start"))
async def cmd_start(message: Message):
    conn = None
    try:
        conn = await get_db_connection()
        user_exists = await conn.fetchval(
            CHECK_USER_QUERY,
            message.from_user.id
        )

        if user_exists:
            keyboard = inline_main_menu_keyboard
            await message.answer_photo(
                photo=dgap_photo,
                caption='Главное меню',
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


@router.callback_query(F.data == 'main_menu')
async def cmd_main_menu(callback: CallbackQuery):
    await callback.answer()
    conn = None
    try:
        conn = await get_db_connection()
        user_exists = await conn.fetchval(
            CHECK_USER_QUERY,
            callback.from_user.id
        )

        if user_exists:
            keyboard = inline_main_menu_keyboard
            media = InputMediaPhoto(
                media=dgap_photo,
                filename='profile.png',
                caption='Главное меню'
            )
            await callback.message.edit_media(
                media=media,
                reply_markup=keyboard
            )
        else:
            keyboard = create_new_profile_keyboard()
            await callback.message.edit_text(
                "Добро пожаловать! Для начала создайте профиль.",
                reply_markup=keyboard
            )

    except Exception as e:
        await callback.message.edit_text("❌ Ошибка при загрузке профиля")
        print(f"Error: {e}")

    finally:
        if conn:
            await conn.close()