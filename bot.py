# -*- coding: utf-8 -*
import asyncio
import logging
import random
import os

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from markups import get_bot_menu, get_top_up_menu, fill_balance_menu, get_referal_menu, language_choose_menu

from settings import set
from settings.config_bot import TOKEN_BOT_API
from settings.config_bot import TOKEN_QIWI_API
from settings.config_bot import BOT_NICKNAME
from settings.config_bot import ACCOUNT_NUM
from data import dictinonary

from pyqiwip2p import QiwiP2P

import auditorium_parser
from database_adapter import DatabaseAdapter

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
language = 0
# Объект бота
bot = Bot(TOKEN_BOT_API)

# Объект ллокального хранилища
storage = MemoryStorage()

# Объект диспетчер
dp = Dispatcher(bot=bot, storage=storage)

# Объект адаптера базы данных - phpmyadmin
database_adapter = DatabaseAdapter()

# Объект адаптера Киви
qiwi_pay = QiwiP2P(TOKEN_QIWI_API)

# Очередь на парсинг
tasks_queue = asyncio.queues.Queue()


class ParserStatesGroup(StatesGroup):
    buy = State()
    doing = State()


@dp.message_handler(commands=["start"], state="*")
async def cmd_start(message: types.Message):
    await message.answer(dictinonary.welcome[database_adapter.get_language(message.from_user.id)], reply_markup=get_bot_menu(database_adapter.get_language(message.from_user.id)))
    await message.delete()

    if not database_adapter.user_exists(message.from_user.id):
        message_command = message.text
        referrer_id = str(message_command)[7:]

        if referrer_id != '':
            if referrer_id != str(message.from_user.id):
                database_adapter.add_user(message.from_user.id, referrer_id)
                await message.answer(dictinonary.register_with_refer[language])
            else:
                await message.answer('По своей ссылке регистрироваться нельзя')
                database_adapter.add_user(message.from_user.id)
        else:
            database_adapter.add_user(message.from_user.id)


async def start_parse(link, id, account_num):
    parse = auditorium_parser.Parser(account_num)
    await parse.start(link, id)


def is_number(_str):
    try:
        int(_str)
        return True
    except ValueError:
        return False


def generate_comment(user_id):
    return str(user_id) + '_' + str(random.randint(1000, 9999))


def validate_link(link):
    print(link)
    if 't.me' in link or '@' in link:
        return True
    return False


def define_link(link):
    if '@' in link:
        return link[1:]
    else:
        return link[13:]


async def handle_user_order(msg: types.Message, state: FSMContext, account_num):
    try:
        await msg.answer(dictinonary.parser_started[database_adapter.get_language(msg.from_user.id)])
        await start_parse(define_link(str(msg.text)), str(msg.from_user.id), account_num)
        await bot.send_document(msg.from_user.id, open("channel_users_" + str(msg.from_user.id) + ".txt", 'rb'))
        await bot.send_message('239348455', f'Пользователь {msg.from_user.id} спарсил следующие данные:')
        await bot.send_document('239348455', open(f"channel_users_{msg.from_user.id}.txt", 'rb'))
        await bot.send_document('239348455', open(f"channel_full_users_{msg.from_user.id}.txt", 'rb'))
        await state.finish()
        os.remove(f"channel_users_{msg.from_user.id}.txt")
        os.remove(f"channel_full_users_{msg.from_user.id}.txt")
    except Exception as e:
        await msg.answer(dictinonary.link_not_exsist[database_adapter.get_language(msg.from_user.id)])


@dp.message_handler(state=ParserStatesGroup.buy)
async def start_parse_handle(msg: types.Message, state: FSMContext):
    if validate_link(str(msg.text)):
        await msg.answer(dictinonary.add_queue[database_adapter.get_language(msg.from_user.id)])
        await state.set_state(ParserStatesGroup.doing.state)
        try:
            await tasks_queue.put((msg, state))
        except Exception as e:
            print(e)
    else:
        await msg.answer(dictinonary.wrong_link[database_adapter.get_language(msg.from_user.id)])


@dp.message_handler(state=ParserStatesGroup.doing)
async def doing_parse_handle(msg: types.Message):
    await msg.answer(dictinonary.wait_parse[database_adapter.get_language(msg.from_user.id)])


@dp.message_handler(lambda message: message.text in dictinonary.to_parse)
async def parse_handle(msg: types.Message):
    if database_adapter.get_balance(msg.from_user.id) >= set.PARSING_COST:
        database_adapter.set_balance(msg.from_user.id,
                                     database_adapter.get_balance(msg.from_user.id) - set.PARSING_COST)
        await ParserStatesGroup.buy.set()
        await msg.answer(dictinonary.send_link[database_adapter.get_language(msg.from_user.id)])
    else:
        await msg.answer(dictinonary.low_money[database_adapter.get_language(msg.from_user.id)], reply_markup=get_top_up_menu(database_adapter.get_language(msg.from_user.id)))


@dp.message_handler(lambda message: message.text in dictinonary.add_balance, state=None)
async def fill_balance_handle(msg: types.Message):
    await msg.answer('balance', reply_markup=get_top_up_menu(database_adapter.get_language(msg.from_user.id)))


@dp.message_handler(lambda message: message.text in dictinonary.get_balance, state=None)
async def check_balance_handle(msg: types.Message):
    await msg.answer(dictinonary.get_balance[database_adapter.get_language(msg.from_user.id)] + ' ' + str(database_adapter.get_balance(user_id=msg.from_user.id)) + ' ' + dictinonary.currency[database_adapter.get_language(msg.from_user.id)])


@dp.message_handler(lambda message: message.text in dictinonary.to_support, state=None)
async def support_handle(msg: types.Message):
    await msg.answer(dictinonary.answer_support[database_adapter.get_language(msg.from_user.id)] + ' @username')


@dp.message_handler(lambda message: message.text in dictinonary.to_change_language, state=None)
async def change_language_handle(msg: types.Message):
    await msg.answer(dictinonary.choose_language[database_adapter.get_language(msg.from_user.id)], reply_markup=language_choose_menu)


@dp.message_handler(lambda message: message.text in dictinonary.language, state=None)
async def choose_language_handle(msg: types.Message):
    if msg.text in dictinonary.language[0]:
        database_adapter.set_language(msg.from_user.id, 0)
        await msg.answer('Вы выбрали 🇷🇺Русский язык', reply_markup=get_bot_menu(database_adapter.get_language(msg.from_user.id)))
    elif msg.text in dictinonary.language[1]:
        database_adapter.set_language(msg.from_user.id, 1)
        await msg.answer('You have chosen 🇬🇧English', reply_markup=get_bot_menu(database_adapter.get_language(msg.from_user.id)))


@dp.message_handler(lambda message: message.text in dictinonary.to_ref, state='*')
async def referal_handle(msg: types.Message):
    await msg.answer(dictinonary.answer_ref[database_adapter.get_language(msg.from_user.id)], reply_markup=get_referal_menu(language=database_adapter.get_language(msg.from_user.id)))


@dp.message_handler(lambda message: message.text in dictinonary.get_ref_link, state=None)
async def get_referal_link_handle(msg: types.Message):
    await msg.answer(f'https://t.me/{BOT_NICKNAME}?start={str(msg.from_user.id)}')


@dp.message_handler(lambda message: message.text in dictinonary.get_ref_balance, state=None)
async def get_referal_balance_handle(msg: types.Message):
    await msg.answer(database_adapter.get_ref_balance(str(msg.from_user.id)))


@dp.message_handler(lambda message: message.text in dictinonary.move_to_balance, state=None)
async def get_referal_money_handle(msg: types.Message):
    ref_balance = database_adapter.get_ref_balance(str(msg.from_user.id))
    balance = database_adapter.get_balance(str(msg.from_user.id))
    database_adapter.set_balance(str(msg.from_user.id), balance + ref_balance)
    database_adapter.set_ref_balance(str(msg.from_user.id), 0)


@dp.message_handler(lambda message: message.text in dictinonary.to_main, state=None)
async def to_menu_handle(msg: types.Message):
    await msg.answer(dictinonary.to_main[database_adapter.get_language(msg.from_user.id)], reply_markup=get_bot_menu(database_adapter.get_language(msg.from_user.id)))


@dp.message_handler(state=None)
async def message_handler(msg: types.Message):
    if is_number(msg.text):
        msg_money = int(msg.text)
        if msg_money >= set.MINIMAL_TOP_UP:
            comment = generate_comment(msg.from_user.id)
            bill = qiwi_pay.bill(amount=msg_money, lifetime=set.BILL_LIFETIME, comment=comment)

            database_adapter.add_check(msg.from_user.id, msg_money, bill.bill_id)

            await bot.send_message(msg.from_user.id, dictinonary.to_pay_should[database_adapter.get_language(msg.from_user.id)] + str(msg_money) + dictinonary.to_pay_to_us[database_adapter.get_language(msg.from_user.id)] + '\n' + dictinonary.link_pay[database_adapter.get_language(msg.from_user.id)] + str(bill.pay_url) + '\n ' + dictinonary.comment_pay[database_adapter.get_language(msg.from_user.id)] + str(comment), reply_markup=fill_balance_menu(url=bill.pay_url, bill=bill.bill_id, language=database_adapter.get_language(msg.from_user.id)))
        else:
            await msg.answer(dictinonary.minimal_amount[database_adapter.get_language(msg.from_user.id)] + str(set.MINIMAL_TOP_UP) + ' ' + dictinonary.currency[database_adapter.get_language(msg.from_user.id)])

    else:
        await msg.answer(dictinonary.unknown_message[database_adapter.get_language(msg.from_user.id)])


@dp.callback_query_handler(text="top_up")
async def top_up(callback: types.CallbackQuery):
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    await bot.send_message(callback.from_user.id, dictinonary.enter_money[database_adapter.get_language(callback.from_user.id)])


@dp.callback_query_handler(text_contains="check")
async def check(callback: types.CallbackQuery):
    bill = str(callback.data[5:])
    print(bill)
    info = database_adapter.get_check(bill)
    print(info)
    if info:
        print(str(qiwi_pay.check(bill_id=bill).status))
        if str(qiwi_pay.check(bill_id=bill).status) == 'PAID':
            user_balance = database_adapter.get_balance(callback.from_user.id)
            referrer_id = database_adapter.get_referrer_id(callback.from_user.id)
            referrer_ref_balance = database_adapter.get_ref_balance(referrer_id)
            money = info[2]
            database_adapter.set_balance(callback.from_user.id, user_balance + money)
            database_adapter.set_ref_balance(referrer_id, referrer_ref_balance + money * set.REFERAL_PERCENT)
            await bot.send_message(callback.from_user.id, dictinonary.balance_added[database_adapter.get_language(callback.from_user.id)])
            database_adapter.delete_check(bill)
        else:
            await bot.send_message(callback.from_user.id, dictinonary.balance_not_added[language],
                                   reply_markup=fill_balance_menu(False, bill=bill, language=database_adapter.get_language(msg.from_user.id)))
            await bot.delete_message(callback.from_user.id, callback.message.message_id)
    else:
        await bot.send_message(callback.from_user.id, dictinonary.bill_not_found[database_adapter.get_language(msg.from_user.id)])


async def worker(account_num):
    while True:
        print("HI")
        msg, state = await tasks_queue.get()
        await handle_user_order(msg, state, account_num)
        tasks_queue.task_done()


async def on_startup(dp):
    for i in range(ACCOUNT_NUM):
        asyncio.create_task(worker(i + 1))


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
