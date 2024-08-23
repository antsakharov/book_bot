import re

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from fsm.states import FSMPressedButton
from database.database import get_user_data,insert_user,update_user_data
from filters.filters import IsDelBookmarkCallbackData, IsDigitCallbackData
from keyboards.bookmarks_kb import create_bookmarks_keyboard, create_edit_keyboard
from keyboards.pagination_kb import create_pagination_keyboard
from lexicon.lexicon import LEXICON
from services.file_handling import book
from services.utils import msg_delete

router = Router()


# Этот хэндлер будет срабатывать на команду "/start" -
# добавлять пользователя в базу данных, если его там еще не было
# и отправлять ему приветственное сообщение
@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(LEXICON[message.text])
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    if not user_data:
        await insert_user({
            'user_id': user_id,
            'page': 1,
            'bookmarks': [],
            'user_state': False,
            'message_id': 0
        })
    else:
        await update_user_data({'user_id': user_id},
                               {'page': 1, 'bookmarks': [], 'user_state': False, 'message_id': 0})


# Этот хэндлер будет срабатывать на команду "/help"
# и отправлять пользователю сообщение со списком доступных команд в боте
@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(LEXICON[message.text])


# Этот хэндлер будет срабатывать на команду "/beginning"
# и отправлять пользователю первую страницу книги с кнопками пагинации
@router.message(Command(commands='beginning'))
async def process_beginning_command(message: Message):
    user_id = message.from_user.id
    await update_user_data({'user_id': user_id}, {'page': 1})
    # Получаем текст для отправки
    user_data = await get_user_data(user_id)
    page = user_data['page']
    text = book[page]
    await message.answer(
        text=text,
        reply_markup=create_pagination_keyboard(
            'backward',
            f'{page}/{len(book)}',
            'navigation',
            # 'find',
            'forward'
        )
    )


# Этот хэндлер будет срабатывать на команду "/continue"
# и отправлять пользователю страницу книги, на которой пользователь
# остановился в процессе взаимодействия с ботом
@router.message(Command(commands='continue'))
async def process_continue_command(message: Message):
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    page = user_data['page']
    text = book[page]
    await message.answer(
        text=text,
        reply_markup=create_pagination_keyboard(
            'backward',
            f'{page}/{len(book)}',
            'navigation',
            # 'find',
            'forward'
        )
    )


# Этот хэндлер будет срабатывать на команду "/bookmarks"
# и отправлять пользователю список сохраненных закладок,
# если они есть или сообщение о том, что закладок нет
@router.message(Command(commands='bookmarks'))
async def process_bookmarks_command(message: Message):
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    if not user_data:
        await message.answer(text=LEXICON['no_bookmarks'])
        return
    if user_data["bookmarks"]:
        keyboard = create_bookmarks_keyboard(*user_data["bookmarks"])
        await message.answer(
            text=LEXICON[message.text],
            reply_markup=keyboard
        )
    else:
        await message.answer(text=LEXICON['no_bookmarks'])

# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки "вперед"
# во время взаимодействия пользователя с сообщением-книгой
@router.callback_query(F.data == 'forward')
async def process_forward_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await get_user_data(user_id)
    page = user_data['page']
    if page < len(book):
        next_page = page + 1
        await update_user_data({'user_id': user_id}, {'page': next_page})
        text = book[next_page]
        await callback.message.edit_text(
            text=text,
            reply_markup=create_pagination_keyboard(
                'backward',
                f'{next_page}/{len(book)}',
                'navigation',
                # 'find',
                'forward'
            )
        )
    await callback.answer()


# Этот хэндлер будет срабатывать при нажатии кнопки навигации по страницам
@router.callback_query(F.data == 'navigation')
async def process_navigation_press(callback: CallbackQuery, state:FSMContext):
    # Устанавливаем состояние
    await state.set_state(FSMPressedButton.waiting_for_message)
    # Сохраняем данные для изменения текста сообщения
    await state.update_data(msg_id = callback.message.message_id,
                            chat_id = callback.message.chat.id)

    # Отправляем сообщение пользователю с запросом о номере страницы
    msg_for_user = await callback.message.answer(text='Введите номер страницы для перехода')
    await callback.answer()
    await msg_delete(msg_for_user, 4)


# Этот хэндлер будет обрабатывать ответ пользователя с номером странцы
@router.message(StateFilter(FSMPressedButton.waiting_for_message))
async def navigation(message: Message, state: FSMContext):
    pattern = r'^[-+]?[0-9]*$'
    user_id = message.from_user.id
    data = await state.get_data()
    if re.match(pattern, message.text):
            page_number = int(message.text)
            await message.delete()
            if 1 <= page_number <= len(book):
                await update_user_data({'user_id': user_id}, {'page': page_number})
                text = book[page_number]
                await message.bot.edit_message_text(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('msg_id'),
                    text=text,
                    reply_markup=create_pagination_keyboard(
                        'backward',
                        f'{page_number}/{len(book)}',
                        'navigation',
                        # 'find',
                        'forward'
                    )
                )
            else:
                msg_for_user1 = await message.answer(text="Номер страницы должен быть в диапазоне от 1 до последней станицы книги")
                await msg_delete(msg_for_user1, 4)
    else:
        msg_for_user2 = await message.answer(text="Нажмите на кнопку выбора страницы и введите корректный номер страницы")
        await msg_delete(msg_for_user2, 4)
    await state.clear()

# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки "назад"
# во время взаимодействия пользователя с сообщением-книгой
@router.callback_query(F.data == 'backward')
async def process_backward_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await get_user_data(user_id)
    page = user_data['page']
    if page > 1:
        previous_page = page - 1
        await update_user_data({'user_id': user_id}, {'page': previous_page})
        text = book[previous_page]
        await callback.message.edit_text(
            text=text,
            reply_markup=create_pagination_keyboard(
                'backward',
                f'{previous_page}/{len(book)}',
                'navigation',
                # 'find',
                'forward'
            )
        )
    await callback.answer()


# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# с номером текущей страницы и добавлять текущую страницу в закладки
@router.callback_query(lambda x: '/' in x.data and x.data.replace('/', '').isdigit())
async def process_page_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await get_user_data(user_id)
    page = user_data['page']
    bookmarks = user_data['bookmarks']
    if page not in bookmarks:
        await update_user_data({'user_id': user_id}, {'bookmarks': bookmarks + [page]})
    await callback.answer('Страница добавлена в закладки!')


# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# с закладкой из списка закладок
@router.callback_query(IsDigitCallbackData())
async def process_bookmark_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    text = book[int(callback.data)]
    await update_user_data({'user_id': user_id}, {'page': int(callback.data)})
    user_data = await get_user_data(user_id)
    page = user_data['page']
    await callback.message.edit_text(
        text=text,
        reply_markup=create_pagination_keyboard(
            'backward',
            f'{page}/{len(book)}',
            'navigation',
            # 'find',
            'forward'
        )
    )


# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# "редактировать" под списком закладок
@router.callback_query(F.data == 'edit_bookmarks')
async def process_edit_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await get_user_data(user_id)
    bookmarks = user_data['bookmarks']
    await callback.message.edit_text(
        text=LEXICON[callback.data],
        reply_markup=create_edit_keyboard(
            *bookmarks
        )
    )


# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# "отменить" во время работы со списком закладок (просмотр и редактирование)
@router.callback_query(F.data == 'cancel')
async def process_cancel_press(callback: CallbackQuery):
    await callback.message.edit_text(text=LEXICON['cancel_text'])


# Этот хэндлер будет срабатывать на нажатие инлайн-кнопки
# с закладкой из списка закладок к удалению
@router.callback_query(IsDelBookmarkCallbackData())
async def process_del_bookmark_press(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = await get_user_data(user_id)
    bookmarks = [bookmark for bookmark in user_data['bookmarks'] if bookmark != int(callback.data[:-3])]
    await update_user_data({'user_id': user_id}, {'bookmarks': bookmarks})
    if bookmarks:
        await callback.message.edit_text(
            text=LEXICON['/bookmarks'],
            reply_markup=create_edit_keyboard(*bookmarks)
        )
    else:
        await callback.message.edit_text(text=LEXICON['no_bookmarks'])