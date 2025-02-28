from aiogram.fsm.state import StatesGroup, State

class Registration(StatesGroup):
    get_name = State()
    get_age = State()
    get_gender = State()
    get_location = State()
    get_photo = State()
