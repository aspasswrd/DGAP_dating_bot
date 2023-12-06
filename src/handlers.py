import random
from os import remove

from aiogram import types, F
from aiogram.types import KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.settings import dp, db, bot
from start import show_profile, SearchPair, CreateProfile


@dp.message(Command("start"))
async def start(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Начать"),
            types.KeyboardButton(text="/Info")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Взлетаем брат",
        one_time_keyboard=False
    )
    await message.answer("Салам 👋\nНажми на кнопку", reply_markup=keyboard)
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.username, message.from_user.id, message.from_user.full_name)


@dp.message(Command("Info"))
async def info_message(message: types.Message):
    await message.answer("Тут будет инфа по боту")


@dp.message(F.text == "Начать")
async def magic_start(message: types.Message):
    kb_exists = [
        [
            KeyboardButton(text='Найти парочку')
        ],
        [
            KeyboardButton(text='Посмотреть свою анкету')
        ],
        [
            KeyboardButton(text='Пересоздать анкету')
        ],
        [
            KeyboardButton(text='Удалить анкету')
        ]
    ]

    kb_not_exists = [
        [
            KeyboardButton(text='Создать анкету'),
        ],
    ]

    if not db.profile_exists(message.from_user.id):
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb_not_exists,
            resize_keyboard=True,
            input_field_placeholder="ЖМИ",
            one_time_keyboard=True
        )
        await message.answer("Чтобы пользоваться ботом надо сначала создать свою анкету", reply_markup=keyboard)
    else:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb_exists,
            resize_keyboard=True,
            input_field_placeholder="ЖМИ",
            one_time_keyboard=False
        )
        await message.answer("Выбирай что хочешь сделать", reply_markup=keyboard)


@dp.message(F.text == "Посмотреть свою анкету")
async def check_profile(message: types.Message):
    await show_profile(message.from_user.id, message.from_user.id)


@dp.message(F.text == "Найти парочку")
async def start_of_search(message: types.Message, state: FSMContext):
    user_data = db.get_info(message.from_user.id)
    city = user_data[4]
    sex = user_data[6]
    pairs_list = db.search_profile(city, sex)
    await state.update_data(
        user=message.from_user.id,
        pairs_list=pairs_list
    )
    await state.set_state(SearchPair.SearchStart)
    await find_pair(message, state)


@dp.message(SearchPair.SearchStart)
async def find_pair(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pairs_list = data['pairs_list']
    user = data['user']
    if len(pairs_list) == 0:
        await message.answer("Чет никого нет подходящего\nПользователей из твоего города видимо нет(((")
        await state.set_state(None)
        await magic_start(message)
    else:
        pair = random.choice(pairs_list)
        await show_profile(user, pair[0])
        kb = [
            [
                KeyboardButton(text='👍'),
                KeyboardButton(text='👎'),
                KeyboardButton(text='❌')
            ],
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="ЖМИ",
            one_time_keyboard=False
        )
        await message.answer("Как тебе этот вариантик?", reply_markup=keyboard)
        await state.update_data(current_pair_id=pair[0])
        await state.set_state(SearchPair.InActiveSearch)


@dp.message(SearchPair.InActiveSearch, F.text == '👍')
async def liked(message: types.Message, state: FSMContext):
    data = await state.get_data()
    pair = data['current_pair_id']
    await bot.send_message(pair, f"Ты понравился(-ась) @{message.from_user.username}")
    await message.answer("Отправил сообщение тому, кто тебе понравился)")
    await state.set_state(SearchPair.SearchStart)
    await find_pair(message, state)


@dp.message(SearchPair.InActiveSearch, F.text == '👎')
async def disliked(message: types.Message, state: FSMContext):
    await state.set_state(SearchPair.SearchStart)
    await find_pair(message, state)


@dp.message(SearchPair.InActiveSearch, F.text == '❌')
async def end_searching(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await magic_start(message)


@dp.message(F.text == "Создать анкету")
async def create_profile(message: types.Message, state: FSMContext):
    if not db.profile_exists(message.from_user.id):
        await message.answer("Для того что бы создать твою so style анкету нужно заполнить несколько пунктов\nДавайте начнём с твоего имя, как мне тебя называть?😉")
        await state.set_state(CreateProfile.name)
    else:
        await message.answer('У тебя уже есть активная анкета\n\n')


@dp.message(CreateProfile.name)
async def get_profile_name(message: types.Message, state: FSMContext):
    kb = [
        [
            KeyboardButton(text="М"),
            KeyboardButton(text="Ж")
        ],
    ]

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="ЖМИ",
        one_time_keyboard=True
    )

    if len(str(message.text)) < 35:
        await state.update_data(profile_name=message.text.lower().title())
        await message.reply(
            message.text.title() + ' - четкое имя😉\nТеперь укажи какого ты пола', reply_markup=keyboard)
        await state.set_state(CreateProfile.sex)
    else:
        await message.answer("Слишком длинное имя")
        return


@dp.message(CreateProfile.sex, F.text == 'М' or F.text == 'Ж')
async def get_profile_sex(message: types.Message, state: FSMContext):
    await state.update_data(profile_sex=message.text)
    await message.reply("Теперь напиши сколько тебе лет")
    await state.set_state(CreateProfile.age)


@dp.message(CreateProfile.sex, F.text != 'М' and F.text != 'Ж')
async def anti_debil(message: types.Message, state: FSMContext):
    await message.answer("Совсем ту-ту\nКнопки для кого сделаны?")


@dp.message(CreateProfile.age)
async def get_profile_age(message: types.Message, state: FSMContext):
    if int(message.text) > 100 or int(message.text) < 10:
        await message.answer("Не понимаю, блокирую\nВведи реальный возраст")
        return
    await state.update_data(profile_age=int(message.text))
    await message.reply(
        message.text + ' - да ты в самом расцвете сил\nТеперь придумай описание своего профиля')
    await state.set_state(CreateProfile.description)


@dp.message(CreateProfile.description)
async def get_profile_description(message: types.Message, state: FSMContext):
    await state.update_data(profile_description=message.text)
    await message.reply("Четко!\nУкажи из какого ты города")
    await state.set_state(CreateProfile.city)


@dp.message(CreateProfile.city)
async def get_profile_city(message: types.Message, state: FSMContext):
    if db.city_exists(message.text.lower().title()):
        await state.update_data(profile_city=message.text.lower().title())
        await message.reply("Скинь свою фотку")
        await state.set_state(CreateProfile.photo)
    else:
        await message.answer("Я такого города РФ не знаю")


@dp.message(CreateProfile.photo)
async def get_profile_photo(message: types.Message, state: FSMContext):
    kb = [
        [
            KeyboardButton(text="Скип")
        ],
    ]

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="ЖМИ",
        one_time_keyboard=True
    )
    if message.photo:
        await bot.download(
            message.photo[-1],
            destination=f"photos/{message.from_user.id}.jpg"
        )
        data = await state.get_data()
        sex = data['profile_sex']
        if sex == "М":
            await message.reply("А ты краcавчик)))\nТеперь кинь мне ссылку на другую соц.сеть (Опционально)",
                                reply_markup=keyboard)
        else:
            await message.reply("А ты красотка)))\nТеперь кинь мне ссылку на другую соц.сеть (Опционально)",
                                reply_markup=keyboard)
        await state.set_state(CreateProfile.social_link)
    else:
        await message.answer("Надо все-таки фотку")


@dp.message(CreateProfile.social_link)
async def get_profile_link(message: types.Message, state: FSMContext):
    await state.update_data(profile_link=message.text)
    await message.answer("Теперь все совсем круто, твой профиль полностью заполнен")
    user_data = await state.get_data()
    db.create_profile(message.from_user.id, message.from_user.username, str(user_data['profile_name']),
                      str(user_data['profile_description']), str(user_data['profile_city']),
                      'photos/' + str(message.from_user.id) + '.jpg', str(user_data['profile_sex']),
                      str(user_data['profile_age']), str(user_data['profile_link']))
    await state.set_state(None)
    await magic_start(message)


@dp.message(F.text == "Удалить анкету")
async def delete_profile(message: types.Message):
    if db.profile_exists(message.from_user.id):
        remove(f"src/photos/{message.from_user.id}.jpg")
        db.delete_profile(message.from_user.id)
        await message.answer('Анкета успешно удалена!')
        await magic_start(message)


@dp.message(F.text == "Пересоздать анкету")
async def change_profile(message: types.Message, state: FSMContext):
    if db.profile_exists(message.from_user.id):
        remove(f"src/photos/{message.from_user.id}.jpg")
        db.delete_profile(message.from_user.id)
    await message.answer("Окей, давай заполним твой профиль по новой\nНапиши свое имя")
    await state.set_state(CreateProfile.name)