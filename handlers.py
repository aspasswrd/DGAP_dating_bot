from random import randint

from aiogram.dispatcher import FSMContext
from aiogram import types
from emoji import emojize

from db import BotDataBase
from main import dp, AllStates, bot, main_text, profile_text


def get_profile(list_profiles):
    profile = list_profiles[randint(0, len(list_profiles) - 1)]
    a = profile
    return [show_profile(a[2], a[3], a[4], a[5]), BotDataBase.get_photo_id(a[1])]


def show_profile(NAME, AGE, CITY, TEXT):
    return f'{NAME}\n{AGE}\n{CITY}\n{TEXT}'


@dp.message_handler(commands="start")
async def profile_start(message: types.Message):
    if not BotDataBase.user_exists(message.from_user.id):
        BotDataBase.add_user(message.from_user.id)

    if BotDataBase.profile_exists(message.from_user.id):

        profile = BotDataBase.get_profile_info(message.from_user.id)
        a = profile[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        await bot.send_photo(photo=open(f"photos/{message.from_user.id}.jpg", "rb"), chat_id=message.from_user.id, caption=caption)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3"]
        keyboard.add(*buttons)

        await message.answer(main_text, reply_markup = keyboard)
        await AllStates.menu_answer.set()

    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["ФОПФик", "БМочка"]
        keyboard.add(*buttons)

        await message.answer("Заполним анкету!\nДля начала выберите свой пол", reply_markup=keyboard)
        await AllStates.choosing_gender.set()


@dp.message_handler(state=AllStates.choosing_gender)
async def choose_gender(message: types.Message, state: FSMContext):
    if message.text not in ["ФОПФик", "БМочка"]:
        await message.answer("Выберите вариант из кнопок ниже")
        return
    await state.update_data(gender = message.text.lower())
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["ФОПФики", "БМочки"]
    keyboard.add(*buttons)
    await message.answer("Кто тебя интересует?", reply_markup = keyboard)
    await AllStates.choosing_interest.set()


@dp.message_handler(state=AllStates.choosing_interest)
async def choose_interest(message: types.Message, state: FSMContext):
    if message.text == "ФОПФики" or message.text == "БМочки":
        await state.update_data(interest = message.text.lower())
        await message.answer("Введите своё имя", reply_markup=types.ReplyKeyboardRemove())
        await AllStates.name.set()
    else:
        await message.answer("Выберите вариант из кнопок ниже")
        return


@dp.message_handler(state=AllStates.name)
async def name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько вам лет?")
    await AllStates.age.set()


@dp.message_handler(state=AllStates.age)
async def age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Напишите свой город")
    await AllStates.city.set()


@dp.message_handler(state=AllStates.city)
async def city(message: types.Message, state: FSMContext):
    await state.update_data(city = message.text)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Оставить пустым")

    await message.answer("Введите описание профиля до 200 символов. Можно пропустить.", reply_markup=keyboard)
    await AllStates.text.set()


@dp.message_handler(state=AllStates.text)
async def text(message: types.Message, state: FSMContext):
    if message.text == "Оставить пустым":
        await state.update_data(text='')
    else:
        if len(message.text) > 200:
            await message.answer("Описание должно быть длинной до 200 символов")
            return
        await state.update_data(text=message.text)

    await message.answer("Загрузите своё фото", reply_markup=types.ReplyKeyboardRemove())
    await AllStates.photo.set()


@dp.message_handler(state=AllStates.photo, content_types=["photo"])
async def download_photo(message: types.Message, state: FSMContext):
    await message.photo[-1].download(destination_file=f"photos/{message.from_user.id}.jpg")
    data = await state.get_data()
    d = list(data.values())
    print(d)

    BotDataBase.add_new_profile(message.from_user.id, d[0], d[1], d[2], d[3], d[4], d[5])
    caption = show_profile(d[2], d[3], d[4], d[5])
    await message.answer("Так выглядит твой профиль: ")
    await bot.send_photo(photo=open(f"photos/{message.from_user.id}.jpg", "rb"), caption=caption, chat_id=message.from_user.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["1", "2", "3"]
    keyboard.add(*buttons)
    await message.answer(main_text, reply_markup=keyboard)
    await AllStates.menu_answer.set()


@dp.message_handler(state=AllStates.menu_answer)
async def menu_answer(message: types.Message, state: FSMContext):
    if message.text == "1":
        profile = BotDataBase.get_profile_info(message.from_user.id)
        a = profile[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        list_profiles = BotDataBase.search_profile(message.from_user.id, a[7], a[4], a[3])

        try:
            get_profile(list_profiles)
        except ValueError:
            await message.answer("Никого не могу найти.")

            await bot.send_photo(photo=open(f"photos/{message.from_user.id}.jpg", "rb"), caption=caption, chat_id=message.from_user.id)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ["1", "2", "3", "4"]
            keyboard.add(*buttons)
            await message.answer(profile_text, reply_markup=keyboard)
            await AllStates.my_profile_feedback.set()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [emojize(":beating_heart:"), emojize(":next_track_button:"), "Вернутся назад"]
        keyboard.add(*buttons)
        profile = get_profile(list_profiles)
        caption = profile[0]
        photo_id = profile[1]

        await state.update_data(liked_id = photo_id)
        await bot.send_photo(photo = open(f"photos/{photo_id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id, reply_markup = keyboard)
        await AllStates.profile_reaction.set()
    elif message.text == "2":
        profile = BotDataBase.get_profile_info(message.from_user.id)
        a = profile[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3", "4"]
        keyboard.add(*buttons)
        await message.answer(profile_text, reply_markup = keyboard)
        await AllStates.my_profile_feedback.set()
    elif message.text == "3":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Да", "Нет"]
        keyboard.add(*buttons)
        await message.answer("Вы точно хотите удалить свою анкету?", reply_markup = keyboard)
        await AllStates.delete_confirm.set()
    else:
        await message.answer("Выберите вариант из кнопок ниже")
        return


@dp.message_handler(state=AllStates.profile_reaction)
async def profile_feedback(message: types.Message, state: FSMContext):
    if message.text == emojize(":beating_heart:"):
        data = await state.get_data()
        d = list(data.values())
        profile = BotDataBase.get_profile_info(message.from_user.id)
        a = profile[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        profiles_list = BotDataBase.search_profile(message.from_user.id, data["interest"], data["city"], data["age"])
        liked_id = data["liked_id"]

        await bot.send_message(text = "Вы понравились: ", chat_id = liked_id)
        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), chat_id = liked_id, caption=caption)
        await bot.send_message(text = f"Ссылка на тг - @{message.from_user.username}", chat_id=liked_id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [emojize(":beating_heart:"), emojize(":next_track_button:"), "Вернутся назад"]
        keyboard.add(*buttons)
        profile = get_profile(profiles_list)
        caption = profile[0]
        photo_id = profile[1]

        await bot.send_photo(photo=open(f"photos/{photo_id}.jpg", "rb"), caption=caption, chat_id=message.from_user.id)
        await AllStates.profile_reaction.set()

    elif message.text == emojize(":next_track_button:"):
        data = await state.get_data()
        profiles_list = BotDataBase.search_profile(message.from_user.id, data["interest"], data["city"], data["age"])
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [emojize(":beating_heart:"), emojize(":next_track_button:"), "Вернутся назад"]
        keyboard.add(*buttons)
        caption = get_profile(profiles_list)[0]
        photo_id = get_profile(profiles_list)[1]

        await bot.send_photo(photo = open(f"photos/{photo_id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
        await AllStates.profile_reaction.set()

    elif message.text == "Вернутся назад":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3"]
        keyboard.add(*buttons)
        await message.answer(main_text, reply_markup = keyboard)
        await AllStates.menu_answer.set()
    else:
        await message.answer("Выберите вариант из кнопок")
        return


@dp.message_handler(state=AllStates.delete_confirm)
async def delete_confirm(message: types.Message, state: FSMContext):
    if message.text == "Да":
        BotDataBase.delete_profile(message.from_user.id)
        BotDataBase.delete_user(message.from_user.id)
        await message.answer("Ваша анкета удалена!\nВы можете вернутся сюда в любое время по команде /start", reply_markup = types.ReplyKeyboardRemove())

    elif message.text == "Нет":
        profile = BotDataBase.get_profile_info(message.from_user.id)
        a = profile[0]
        caption = show_profile(a[2], a[3], a[4], a[5])

        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3", "4"]
        keyboard.add(*buttons)

        await message.answer(profile_text, reply_markup=keyboard)
        await AllStates.my_profile_feedback.set()
    else:
        await message.answer("Выберите вариант из кнопок ниже")
        return
