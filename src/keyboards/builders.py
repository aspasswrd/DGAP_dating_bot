from aiogram import types

def main_menu_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🔍 Поиск")],
            [types.KeyboardButton(text="👤 Мой профиль")],
            [types.KeyboardButton(text="❌ Удалить профиль")]
        ],
        resize_keyboard=True
    )

def create_new_profile_keyboard():
    return types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="Создать профиль")]
                ],
                resize_keyboard=True
            )
