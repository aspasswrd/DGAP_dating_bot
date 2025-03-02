from aiogram.utils.media_group import MediaGroupBuilder
from aiogram import F, Router
from aiogram.types import CallbackQuery, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from .common import dgap_photo
from ..config import get_db_connection
from ..database.queries import FIND_MATCH_QUERY, SELECT_USER_PHOTO_QUERY
from ..keyboards.builders import match_keyboard, inline_main_menu_keyboard

router = Router()

@router.callback_query(F.data == 'find_match')
async def find_match(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    conn = await get_db_connection()

    try:
        matches = await conn.fetch(FIND_MATCH_QUERY, callback.from_user.id)
        await conn.close()
        if not matches:
            media = InputMediaPhoto(
                media=dgap_photo,
                caption="😔 Нет подходящих пользователей. Попробуйте позже."
            )
            await callback.message.edit_media(media=media, reply_markup=inline_main_menu_keyboard)
            return

        await state.update_data(matches=matches, current_index=0)
        await show_next_profile(callback, state)

    except Exception as e:
        print(f"Error: {e}")
        await callback.answer("❌ Ошибка поиска")
    finally:
        await conn.close()


@router.callback_query(F.data == 'next_profile')
async def show_next_profile(callback: CallbackQuery, state: FSMContext):
    conn = await get_db_connection()
    data = await state.get_data()
    index = data['current_index']
    matches = data['matches']

    if index >= len(matches):
        media = InputMediaPhoto(
            media=dgap_photo,
            caption="💔 Эта стопка кончилась(\nМожешь создать новую"
        )
        await callback.message.edit_media(media=media, reply_markup=inline_main_menu_keyboard)
        await state.clear()
        return

    user = matches[index]
    photos = await conn.fetch(SELECT_USER_PHOTO_QUERY, user['user_id'])

    caption = (
        f"[{index + 1}/{len(matches)}]\n"
        f"👤 {user['name']}, {user['age']}\n"
        f"📍 {round(user['distance_km'])} км от вас"
    )

    media = InputMediaPhoto(
        media=photos[0]['photo'],
        caption=caption
    )

    await callback.message.edit_media(media=media, reply_markup=match_keyboard)
    await state.update_data(current_index=index + 1)


async def update_match_status(conn, current_user_id, user1, user2, is_like):
    record = await conn.fetchrow(
        "SELECT * FROM bot.match WHERE user_id_1 = $1 AND user_id_2 = $2",
        user1, user2
    )

    if record:
        if is_like:
            column = 'first_to_second' if current_user_id == user1 else 'second_to_first'
            await conn.execute(
                f"UPDATE bot.match SET {column} = true WHERE user_id_1 = $1 AND user_id_2 = $2",
                user1, user2
            )
    else:
        column = 'first_to_second' if current_user_id == user1 else 'second_to_first'
        await conn.execute(
            f"INSERT INTO bot.match (user_id_1, user_id_2, {column}) "
            f"VALUES ($1, $2, $3)",
            user1, user2, is_like
        )

@router.callback_query(F.data == 'like')
async def process_like(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_user_id = callback.from_user.id
    target_user = data['matches'][data['current_index'] - 1]

    conn = await get_db_connection()
    try:
        user1 = min(current_user_id, target_user['user_id'])
        user2 = max(current_user_id, target_user['user_id'])

        await update_match_status(conn, current_user_id, user1, user2, is_like=True)

        await callback.answer(text="Лайк отправлен", show_alert=True)
        await show_next_profile(callback, state)

    except Exception as e:
        print(f"Error: {e}")
        await callback.answer("❌ Ошибка")
    finally:
        await conn.close()

@router.callback_query(F.data == 'dislike')
async def process_dislike(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_user_id = callback.from_user.id
    target_user = data['matches'][data['current_index'] - 1]

    conn = await get_db_connection()
    try:
        user1 = min(current_user_id, target_user['user_id'])
        user2 = max(current_user_id, target_user['user_id'])

        await update_match_status(conn, current_user_id, user1, user2, is_like=False)

        await callback.answer(text="Больше не показываем", show_alert=True)
        await show_next_profile(callback, state)

    except Exception as e:
        print(f"Error: {e}")
        await callback.answer("❌ Ошибка")
    finally:
        await conn.close()
