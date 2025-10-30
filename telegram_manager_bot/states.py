# telegram_manager_bot/states.py
from aiogram.fsm.state import State, StatesGroup

class ManagerAuthStates(StatesGroup):
    waiting_for_email = State()