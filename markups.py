from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

# меню markups
bot_menu = ReplyKeyboardMarkup(resize_keyboard=True)
button_parse = KeyboardButton('💼Спарсить аудиторию (10 руб.)')
button_fill_balance = KeyboardButton('💳Пополнить баланс')
button_check_balance = KeyboardButton('💶Мой баланс')
button_change_language = KeyboardButton('🇷🇺Сменить язык')
button_support = KeyboardButton('🧑‍💻Поддержка')
button_referal = KeyboardButton('👨‍👩‍👧‍👦Реферальная программа')
bot_menu.row(button_parse)
bot_menu.row(button_fill_balance, button_check_balance)
bot_menu.row(button_change_language, button_support)
bot_menu.row(button_referal)

# меню реферальной программы
referal_menu = ReplyKeyboardMarkup(resize_keyboard=True)
button_get_link = KeyboardButton('✍️Получить ссылку')
button_referal_balance = KeyboardButton('💳Реферальный баланс')
button_move_to_balance = KeyboardButton('💶Вывести на основной баланс')
button_to_menu = KeyboardButton('Главное меню')
referal_menu.row(button_get_link, button_referal_balance)
referal_menu.row(button_move_to_balance)
referal_menu.row(button_to_menu)

# inlines buttons

top_up_menu = InlineKeyboardMarkup(row_width=1)
button_top_up = InlineKeyboardButton(text="Пополнить", callback_data="top_up")
top_up_menu.add(button_top_up)

def fill_balance_menu(isUrl=True, url="", bill=""):
    qiwiMenu = InlineKeyboardMarkup(row_width=1)

    if isUrl:
        button_url_qiwi = InlineKeyboardButton(text="Перейти к оплате", url=url)
        qiwiMenu.insert(button_url_qiwi)

    button_check_bill = InlineKeyboardButton(text="Проверить оплату", callback_data="check"+bill)
    qiwiMenu.insert(button_check_bill)

    return qiwiMenu

