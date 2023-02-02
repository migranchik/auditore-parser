import json
import configparser
import time

from telethon.sync import TelegramClient
from telethon import connection

# импрортируем конфигурацию из config.py
from settings import config_parser

# для корректного переноса времени сообщений в json
from datetime import date, datetime

# классы для работы с каналами
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch

# класс для работы с сообщениями
from telethon.tl.functions.messages import GetHistoryRequest


class Parser:

    def __init__(self, account_number):
        # Считываем учетные данные
        config = configparser.ConfigParser()
        config.read(f"account{account_number}.ini")

        # Присваиваем значения внутренним переменным
        self.api_id = config['Telegram']['api_id']
        self.api_hash = config['Telegram']['api_hash']
        self.username = config['Telegram']['username']

        self.client = TelegramClient(self.username, int(self.api_id), self.api_hash)

    # функция считывания имен из базы данных
    def read_name(self, path):
        with open(path, encoding="utf8") as file:
            return file.read()

    # функция записи результата после парсинга
    def write_auditorium(self, users, file, gender):
        file.write('\n')
        file.write(gender)
        file.write('\n')
        file.write('\n')
        for user in users:
            json.dump(user, file, ensure_ascii=False)
            file.write('\n')

    async def dump_all_participants(self, channel, id):
        """Записывает json-файл с информацией о всех участниках канала/чата"""
        offset_user = 0  # номер участника, с которого начинается считывание
        limit_user = 100  # максимальное число записей, передаваемых за один раз

        all_participants = []  # список всех участников канала
        filter_user = ChannelParticipantsSearch('')

        male_names = self.read_name(config_parser.male_names_path)
        female_names = self.read_name(config_parser.female_names_path)

        man_users = []
        woman_users = []
        unknown_users = []

        man_users_json = []
        woman_users_json = []
        unknown_users_json = []

        i = 0
        while True:
            participants = await self.client(GetParticipantsRequest(channel,
                                                               filter_user, offset_user, limit_user, hash=0))
            i += 1
            print('\r', i, end='')
            if not participants.users:
                break

            all_participants.extend(participants.users)
            offset_user += len(participants.users)

        for participant in all_participants:
            if not participant.bot and participant.username is not None:
                if participant.first_name in male_names and len(str(participant.first_name)) >= 3:
                    username = '@' + str(participant.username)
                    man_users.append(username)
                    man_users_json.append({"id": participant.id,
                                           "first_name": participant.first_name,
                                           "last_name": participant.last_name,
                                           "user": participant.username,
                                           "phone": participant.phone,
                                           "is_bot": participant.bot})
                elif participant.first_name in female_names and len(str(participant.first_name)) >= 3:
                    username = '@' + str(participant.username)
                    woman_users.append(username)
                    woman_users_json.append({"id": participant.id,
                                             "first_name": participant.first_name,
                                             "last_name": participant.last_name,
                                             "user": participant.username,
                                             "phone": participant.phone,
                                             "is_bot": participant.bot})
                else:
                    username = '@' + str(participant.username)
                    unknown_users.append(username)
                    unknown_users_json.append({"id": participant.id,
                                               "first_name": participant.first_name,
                                               "last_name": participant.last_name,
                                               "user": participant.username,
                                               "phone": participant.phone,
                                               "is_bot": participant.bot})

        with open('channel_users_' + id + '.txt', 'w', encoding='utf8') as outfile:
            self.write_auditorium(man_users, outfile, '__Мужчины__')
            self.write_auditorium(woman_users, outfile, '__Женщины__')
            self.write_auditorium(unknown_users, outfile, '__Не определено__')

        with open('channel_full_users_' + id + '.txt', 'w', encoding='utf8') as outfile:
            self.write_auditorium(man_users_json, outfile, '__Мужчины__')
            self.write_auditorium(woman_users_json, outfile, '__Женщины__')
            self.write_auditorium(unknown_users_json, outfile, '__Не определено__')

    async def to_parse(self, link, id):
        channel = await self.client.get_entity(link)
        await self.dump_all_participants(channel, id)

    async def start(self, link, id):
        async with self.client:
            self.client.start()
            await self.to_parse(link, id)
