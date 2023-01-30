# -*- coding: utf-8 -*
import asyncio
from multiprocessing import Process
import logging
import random

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Text

from markups import bot_menu, top_up_menu, fill_balance_menu, referal_menu

from settings import set
from settings.config_bot import TOKEN_BOT_API
from settings.config_bot import TOKEN_QIWI_API
from settings.config_bot import BOT_NICKNAME

from pyqiwip2p import QiwiP2P

import auditorium_parser
from database_adapter import DatabaseAdapter

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

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

tasks_queue = asyncio.queues.Queue()


class ParserStatesGroup(StatesGroup):
    buy = State()
    doing = State()


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer('Добро пожаловать!', reply_markup=bot_menu)
    await message.delete()

    if not database_adapter.user_exists(message.from_user.id):
        message_command = message.text
        referrer_id = str(message_command)[7:]

        if referrer_id != '':
            if referrer_id != str(message.from_user.id):
                database_adapter.add_user(message.from_user.id, referrer_id)
                await message.answer(
                    'Вы зарегистрировались по реферальной ссылке, давайте пополним и баланс и приступим к работе)')
            else:
                await message.answer('По своей ссылке регистрироваться нельзя')
                database_adapter.add_user(message.from_user.id)
        else:
            database_adapter.add_user(message.from_user.id)


async def start_parse(link, id):
    parse = auditorium_parser.Parser()
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


async def handle_user_order(msg: types.Message):
    try:
        await msg.answer("Парсер запущен, пожалуйста, ожидайте...")
        await ParserStatesGroup.next()
        await start_parse(define_link(str(msg.text)), str(msg.from_user.id))
        await bot.send_document(msg.from_user.id, open("channel_users_" + str(msg.from_user.id) + ".json", 'rb'))
        await bot.send_document(msg.from_user.id, open("channel_full_users_" + str(msg.from_user.id) + ".json", 'rb'))
        await ParserStatesGroup.next()
    except Exception as e:
        await msg.answer("Чата с данной ссылкой не существует")
        await ParserStatesGroup.next()
        print(e)


@dp.message_handler(lambda message: message.text, state=ParserStatesGroup.buy)
async def start_parse_handle(msg: types.Message):
    if validate_link(str(msg.text)):
        await tasks_queue.put(handle_user_order(msg))
    else:
        await msg.answer("Кажется, отправленная вами ссылка неверная")


@dp.message_handler(lambda message: message.text, state=ParserStatesGroup.doing)
async def doing_parse_handle(msg: types.Message):
    await msg.answer('Ждите, пока данные парсятся')


@dp.message_handler(Text(equals='💼Спарсить аудиторию (10 руб.)', ignore_case=True))
async def parse_handle(msg: types.Message):
    if database_adapter.get_balance(msg.from_user.id) >= set.PARSING_COST:
        database_adapter.set_balance(msg.from_user.id,
                                     database_adapter.get_balance(msg.from_user.id) - set.PARSING_COST)
        await ParserStatesGroup.buy.set()
        await msg.answer('Отправьте ссылку на группу вида: "@group" или "https://t.me..."')
    else:
        await msg.answer('Недостаточно средств...', reply_markup=top_up_menu)


@dp.message_handler(Text(equals='💳Пополнить баланс', ignore_case=True), state=None)
async def fill_balance_handle(msg: types.Message):
    await msg.answer('balance', reply_markup=top_up_menu)


@dp.message_handler(Text(equals='💶Мой баланс', ignore_case=True), state=None)
async def check_balance_handle(msg: types.Message):
    await msg.answer('💰 Ваш баланс: ' + str(database_adapter.get_balance(user_id=msg.from_user.id)) + ' р')


@dp.message_handler(Text(equals='🧑‍💻Поддержка', ignore_case=True), state=None)
async def check_balance_handle(msg: types.Message):
    await msg.answer('По всем вопросам пишите @username')


@dp.message_handler(Text(equals='👨‍👩‍👧‍👦Реферальная программа', ignore_case=True), state=None)
async def referal_handle(msg: types.Message):
    await msg.answer(
        'С каждой суммы пополнения, приглашенного вами пользователя, вы получаете 35% на реферальный баланс. - С реферального баланса вы можете вывести средства на основной счет.',
        reply_markup=referal_menu)


@dp.message_handler(Text(equals='✍️Получить ссылку', ignore_case=True), state=None)
async def get_referal_link_handle(msg: types.Message):
    await msg.answer(f'https://t.me/{BOT_NICKNAME}?start={str(msg.from_user.id)}')


@dp.message_handler(Text(equals='💳Реферальный баланс', ignore_case=True), state=None)
async def get_referal_balance_handle(msg: types.Message):
    await msg.answer(database_adapter.get_ref_balance(str(msg.from_user.id)))


@dp.message_handler(Text(equals='💶Вывести на основной баланс', ignore_case=True), state=None)
async def get_referal_money_handle(msg: types.Message):
    ref_balance = database_adapter.get_ref_balance(str(msg.from_user.id))
    balance = database_adapter.get_balance(str(msg.from_user.id))
    database_adapter.set_balance(str(msg.from_user.id), balance + ref_balance)
    database_adapter.set_ref_balance(str(msg.from_user.id), 0)


@dp.message_handler(Text(equals='Главное меню', ignore_case=True), state=None)
async def to_menu_handle(msg: types.Message):
    await msg.answer('Главное меню', reply_markup=bot_menu)


@dp.message_handler(state=None)
async def message_handler(msg: types.Message):
    if is_number(msg.text):
        msg_money = int(msg.text)
        if msg_money >= set.MINIMAL_TOP_UP:
            comment = generate_comment(msg.from_user.id)
            bill = qiwi_pay.bill(amount=msg_money, lifetime=set.BILL_LIFETIME, comment=comment)

            database_adapter.add_check(msg.from_user.id, msg_money, bill.bill_id)

            await bot.send_message(msg.from_user.id,
                                   f'Вам нужно отправить {msg_money} рублей на наш счет QIWI\nСсылка:{bill.pay_url}\n '
                                   f'Указав комментарий к оплате: {comment}',
                                   reply_markup=fill_balance_menu(url=bill.pay_url, bill=bill.bill_id))
        else:
            await msg.answer('Минимальная сумма для пополнения ' + str(set.MINIMAL_TOP_UP) + ' руб')

    else:
        await msg.answer('К сожалению, я вас не понимаю или эта функция пока в разработке(')


@dp.callback_query_handler(text="top_up")
async def top_up(callback: types.CallbackQuery):
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    await bot.send_message(callback.from_user.id, "Введите сумму для пополнения:")


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
            await bot.send_message(callback.from_user.id, 'Вы пополнили свой баланс!)')
            database_adapter.delete_check(bill)
        else:
            await bot.send_message(callback.from_user.id, 'Вы не оплатили счет!',
                                   reply_markup=fill_balance_menu(False, bill=bill))
            await bot.delete_message(callback.from_user.id, callback.message.message_id)
    else:
        await bot.send_message(callback.from_user.id, 'Счет не найден!')


async def worker():
    while True:
        if tasks_queue.empty():
            continue
        task = await tasks_queue.get()
        await task
        tasks_queue.task_done()


def run_in_parallel(*fns):
    proc = []
    for fn in fns:
        p = Process(target=fn)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()


def bot_start():
    executor.start_polling(dp, skip_updates=True)


def worker_start():
    asyncio.run(worker())


if __name__ == "__main__":
    run_in_parallel(bot_start, worker_start)

