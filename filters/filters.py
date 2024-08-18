from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message



class IsDigitCallbackData(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.isdigit()


class IsDelBookmarkCallbackData(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.data.endswith('del') and callback.data[:-3].isdigit()

class IsDigitMessageText(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        text_condition = message.text.startswith('-') or message.text.isdigit()
        return text_condition