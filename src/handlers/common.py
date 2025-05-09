from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from src.config import get_db_connection, dgap_photo
from ..database.queries import CHECK_USER_QUERY, GET_USERS_COUNT_QUERY
from ..keyboards.builders import create_new_profile_keyboard, inline_main_menu_keyboard

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
            users_count = await conn.fetchval(GET_USERS_COUNT_QUERY)

            keyboard = inline_main_menu_keyboard
            await message.answer_photo(
                photo=dgap_photo,
                caption=f"😮‍💨 Главное меню\nКоличество зарегистрированных пользователей: {int(users_count)}",
                reply_markup=keyboard,
            )
        else:
            await state.clear()
            keyboard = create_new_profile_keyboard
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
async def cmd_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer(reply_markup=types.ReplyKeyboardRemove())
    conn = None
    try:
        conn = await get_db_connection()
        user_exists = await conn.fetchval(
            CHECK_USER_QUERY,
            callback.from_user.id
        )

        if user_exists:
            users_count = await conn.fetchval(GET_USERS_COUNT_QUERY)

            keyboard = inline_main_menu_keyboard
            media = InputMediaPhoto(
                media=dgap_photo,
                caption=f"😮‍💨 Главное меню\nКоличество зарегистрированных пользователей: {users_count}"
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