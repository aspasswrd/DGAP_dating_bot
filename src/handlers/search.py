
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram import F, Router
from aiogram.types import CallbackQuery, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from .common import dgap_photo
from ..config import get_db_connection
from ..database.queries import FIND_MATCH_QUERY, SELECT_USER_PHOTO_QUERY
from ..keyboards.builders import match_keyboard, inline_main_menu_keyboard

router = Router()

from ..config import bot

@router.callback_query(F.data == 'find_match')
async def find_match(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    conn = await get_db_connection()

    try:
        matches = await conn.fetch(FIND_MATCH_QUERY, callback.from_user.id)
        if not matches:
            media = InputMediaPhoto(
                media=dgap_photo,
                filename='profile.png',
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


async def show_next_profile(callback: CallbackQuery, state: FSMContext):
    conn = await get_db_connection()
    data = await state.get_data()
    index = data['current_index']
    matches = data['matches']

    if index >= len(matches):
        await callback.message.answer("💔 Больше нет пользователей в поиске")
        await state.clear()
        return

    user = matches[index]
    photos = await conn.fetch(SELECT_USER_PHOTO_QUERY, user['user_id'])

    # Формирование сообщения с медиагруппой
    media = MediaGroupBuilder(caption=(
        f"👤 {user['name']}, {user['age']}\n"
        f"📍 {round(user['distance_km'])} км от вас"
    ))

    for photo in photos:
        media.add_photo(media=BufferedInputFile(photo['photo'], filename='photo.jpg'))

    await callback.message.answer_media_group(media.build())
    await callback.message.answer("Выберите действие:", reply_markup=match_keyboard)
    await state.update_data(current_index=index + 1)


@router.callback_query(F.data == 'like')
async def process_like(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_user_id = callback.from_user.id
    target_user = data['matches'][data['current_index'] - 1]

    conn = await get_db_connection()
    try:
        user1 = min(current_user_id, target_user['user_id'])
        user2 = max(current_user_id, target_user['user_id'])

        # Обновляем запись в таблице match
        record = await conn.fetchrow(
            "SELECT * FROM bot.match WHERE user_id_1 = $1 AND user_id_2 = $2",
            user1, user2
        )

        if record:
            if current_user_id == user1:
                await conn.execute(
                    "UPDATE bot.match SET first_to_second = true WHERE user_id_1 = $1 AND user_id_2 = $2",
                    user1, user2
                )
            else:
                await conn.execute(
                    "UPDATE bot.match SET second_to_first = true WHERE user_id_1 = $1 AND user_id_2 = $2",
                    user1, user2
                )
        else:
            await conn.execute(
                "INSERT INTO bot.match (user_id_1, user_id_2, first_to_second, second_to_first) "
                "VALUES ($1, $2, $3, $4)",
                user1, user2,
                current_user_id == user1,
                current_user_id == user2
            )

        # Проверка на мэтч
        if (current_user_id == user1 and record and record['second_to_first']) or \
                (current_user_id == user2 and record and record['first_to_second']):
            await bot.send_message(
                current_user_id,
                f"💌 У вас мэтч с {target_user['name']}! Напишите: @{target_user['username']}"
            )
            await bot.send_message(
                target_user['user_id'],
                f"💌 У вас мэтч с {callback.from_user.full_name}! Напишите: @{callback.from_user.username}"
            )

        await callback.answer("❤️ Лайк отправлен!")
        await show_next_profile(callback, state)

    except Exception as e:
        print(f"Error: {e}")
        await callback.answer("❌ Ошибка")
    finally:
        await conn.close()
