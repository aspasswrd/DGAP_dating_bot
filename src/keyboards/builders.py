from aiogram import types
from aiogram.types import InlineKeyboardButton

inline_main_menu_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👤 Мой профиль', callback_data='profile')],
    [InlineKeyboardButton(text='Найти пару', callback_data='find_match')]
])

inline_edit_profile_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вернуться в меню', callback_data='main_menu')],
    [InlineKeyboardButton(text='Изменить профиль', callback_data='edit_profile')],
    [InlineKeyboardButton(text='Изменить предпочтения', callback_data='edit_preferences')],
    [InlineKeyboardButton(text='❌ Удалить профиль', callback_data='delete_profile')]
])

create_new_profile_keyboard = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Создать профиль")]
    ],
    resize_keyboard=True
)
