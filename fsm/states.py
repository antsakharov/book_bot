from aiogram.fsm.state import State, StatesGroup

# Cоздаем класс StatesGroup для нашей машины состояний
class FSMPressedButton(StatesGroup):
   waiting_for_message = State()