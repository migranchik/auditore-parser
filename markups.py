from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from data import dictinonary
# меню markups

language_choose_menu = ReplyKeyboardMarkup(resize_keyboard=True)
button_russian = KeyboardButton(dictinonary.language[0])
button_english = KeyboardButton(dictinonary.language[1])
language_choose_menu.row(button_russian, button_english)


def get_bot_menu(language=1):
    bot_menu = ReplyKeyboardMarkup(resize_keyboard=True)
    button_parse = KeyboardButton(dictinonary.to_parse[language])
    button_fill_balance = KeyboardButton(dictinonary.add_balance[language])
    button_check_balance = KeyboardButton(dictinonary.get_balance[language])
    button_change_language = KeyboardButton(dictinonary.to_change_language[language])
    button_support = KeyboardButton(dictinonary.to_support[language])
    button_referal = KeyboardButton(dictinonary.to_ref[language])
    bot_menu.row(button_parse)
    bot_menu.row(button_fill_balance, button_check_balance)
    bot_menu.row(button_change_language, button_support)
    bot_menu.row(button_referal)
    return bot_menu


# меню реферальной программы
def get_referal_menu(language=0):
    referal_menu = ReplyKeyboardMarkup(resize_keyboard=True)
    button_get_ref_link = KeyboardButton(dictinonary.get_ref_link[language])
    button_referal_balance = KeyboardButton(dictinonary.get_ref_balance[language])
    button_move_to_balance = KeyboardButton(dictinonary.move_to_balance[language])
    button_to_menu = KeyboardButton(dictinonary.to_main[language])
    referal_menu.row(button_get_ref_link, button_referal_balance)
    referal_menu.row(button_move_to_balance)
    referal_menu.row(button_to_menu)
    return referal_menu


# inlines buttons
def get_top_up_menu(language=0):
    top_up_menu = InlineKeyboardMarkup(row_width=1)
    button_top_up = InlineKeyboardButton(text="Пополнить", callback_data="top_up")
    top_up_menu.add(button_top_up)
    return top_up_menu


def fill_balance_menu(isUrl=True, url="", bill="", language=0):
    qiwiMenu = InlineKeyboardMarkup(row_width=1)

    if isUrl:
        button_url_qiwi = InlineKeyboardButton(text=dictinonary.redirect_to_pay[language], url=url)
        qiwiMenu.insert(button_url_qiwi)

    button_check_bill = InlineKeyboardButton(text=dictinonary.check_pay[language], callback_data="check"+bill)
    qiwiMenu.insert(button_check_bill)

    return qiwiMenu

