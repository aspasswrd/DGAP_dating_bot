from aiogram.fsm.state import StatesGroup, State

class Preferences(StatesGroup):
    start_editing = State()
    get_min_age = State()
    get_max_age = State()
    get_radius = State()
