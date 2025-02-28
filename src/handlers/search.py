from aiogram import types, F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from ..config import get_db_connection
from ..database.queries import FIND_MATCH_QUERY, SELECT_USER_PHOTO_QUERY

router = Router()

@router.message(F.text == "🔍 Поиск")
async def start_search(message: Message, state: FSMContext):
    conn = None
    try:
        conn = await get_db_connection()
        # Получаем первого подходящего пользователя
        target = await conn.fetchrow(
            FIND_MATCH_QUERY,
            message.from_user.id
        )

        if target:
            photo = await conn.fetchrow(
                SELECT_USER_PHOTO_QUERY,
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

            #await state.set_state(MainMenu.view_profile)
        else:
            await message.answer("😞 Пока нет подходящих анкет. Попробуйте позже!")

    except Exception as e:
        await message.answer("❌ Ошибка при поиске")
        print(f"Error: {e}")

    finally:
        if conn:
            await conn.close()
