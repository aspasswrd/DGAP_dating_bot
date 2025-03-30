from aiogram import F, Router, types
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton

from .common import dgap_photo
from ..config import get_db_connection
from ..database.queries import GET_STACK_QUERY, SELECT_USER_PHOTO_QUERY, GET_MATCHES_QUERY, RECORD_MATCH_QUERY, \
    GET_MATCH_STATUS_QUERY, GET_USER_INTERESTS_QUERY
from ..keyboards.builders import match_keyboard, inline_main_menu_keyboard

router = Router()

@router.callback_query(F.data == 'find_match')
async def find_match(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    conn = await get_db_connection()

    try:
        stack = await conn.fetch(GET_STACK_QUERY, callback.from_user.id)
        await conn.close()
        if not stack:
            media = InputMediaPhoto(
                media=dgap_photo,
                caption="😔 Нет подходящих пользователей. Можешь увеличить радиус поиска в настройках профиля"
            )
            await callback.message.edit_media(media=media, reply_markup=inline_main_menu_keyboard)
            return

        await state.update_data(matches=stack, current_index=0)
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
            caption="💔 Эта стопка кончилась(\nМожешь создать новую\nP.S. Если стопка слишком маленькая можешь увеличить радиус поиска в настройках профиля"
        )
        await callback.message.edit_media(media=media, reply_markup=inline_main_menu_keyboard)
        await state.clear()
        return

    user = matches[index]

    # Получаем фото и интересы пользователя
    photos = await conn.fetch(SELECT_USER_PHOTO_QUERY, user['user_id'])
    interests = await conn.fetch(
        GET_USER_INTERESTS_QUERY,
        user['user_id']
    )

    # Формируем список интересов
    interests_text = "\n🎯 Интересы: "
    if interests:
        interests_text += ", ".join([i['name'] for i in interests])
    else:
        interests_text += "не указаны"

    caption = (
        f"[{index + 1}/{len(matches)}]\n"
        f"👤 {user['name']}, {user['age']}\n"
        f"📍 {round(user['distance_km'])} км от вас"
        f"{interests_text}"
    )

    media = InputMediaPhoto(
        media=photos[0]['photo'],
        caption=caption
    )

    await callback.message.edit_media(media=media, reply_markup=match_keyboard)
    await state.update_data(current_index=index + 1)
    await conn.close()


async def update_match_status(conn, current_user_id, user1, user2, is_like):
    column = 'first_to_second' if current_user_id == user1 else 'second_to_first'

    await conn.execute(f"""
        INSERT INTO bot.match (user_id_1, user_id_2, {column})
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id_1, user_id_2) 
        DO UPDATE SET {column} = EXCLUDED.{column}
        """,
        user1, user2, is_like)

    match_record = await conn.fetchrow(
        GET_MATCH_STATUS_QUERY,
        user1, user2
    )

    if match_record and match_record['first_to_second'] and match_record['second_to_first']:
        await conn.execute(RECORD_MATCH_QUERY, user1, user2)


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

@router.callback_query(F.data == 'get_match')
async def get_matches(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    conn = await get_db_connection()

    try:
        matches = await conn.fetch(GET_MATCHES_QUERY, callback.from_user.id)
        await conn.close()

        if not matches:
            media = InputMediaPhoto(
                media=dgap_photo,
                caption="🤷‍♂️ У вас пока нет мэтчей."
            )
            await callback.message.edit_media(media=media, reply_markup=inline_main_menu_keyboard)
            return


        await state.update_data(matches=matches, current_index=0, is_matches_mode=True)
        await show_next_match(callback, state)

    except Exception as e:
        print(f"Error: {e}")
        await callback.answer("❌ Ошибка загрузки мэтчей")
    finally:
        await conn.close()

@router.callback_query(F.data == 'next_match')
async def next_match_handler(callback: CallbackQuery, state: FSMContext):
    await show_next_match(callback, state)


async def show_next_match(callback: CallbackQuery, state: FSMContext):
    conn = await get_db_connection()
    data = await state.get_data()
    index = data['current_index']
    matches = data['matches']

    if index >= len(matches):
        media = InputMediaPhoto(
            media=dgap_photo,
            caption="🏁 Это все ваши мэтчи!"
        )
        await callback.message.edit_media(media=media, reply_markup=inline_main_menu_keyboard)
        await state.clear()
        return

    match = matches[index]
    photos = await conn.fetch(SELECT_USER_PHOTO_QUERY, match['matched_user_id'])

    caption = (
        f"[{index + 1}/{len(matches)}]\n"
        f"👤 {match['name']}, {match['age']}\n"
        f"💌 Юзернейм: @{match['matched_username']}\n"
        f"🔗 Ссылка: https://t.me/{match['matched_username']}"
    )

    media = InputMediaPhoto(
        media=photos[0]['photo'] if photos else dgap_photo,
        caption=caption
    )

    match_view_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий", callback_data='next_match')],
        [InlineKeyboardButton(text="Написать", url=f"https://t.me/{match['matched_username']}")],
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ])

    await callback.message.edit_media(media=media, reply_markup=match_view_keyboard)
    await state.update_data(current_index=index + 1)