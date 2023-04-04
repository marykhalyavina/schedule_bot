from os import path
import json
from telebot import types
import telebot
import requests
from bs4 import BeautifulSoup
from telebot import TeleBot, types
import re

API_TOKEN = '5674823347:AAFn9doTcoZB9mIrHROslMaySG-CvR33Bvo'

bot = telebot.TeleBot(API_TOKEN)
path_to_json = 'schedule.json'
classroom = '14-103'


def connection_for_parsing():
    link = "https://www.vyatsu.ru/reports/schedule/room/14_1_29082022_11092022.html"
    connection = requests.get(link)
    connection.encoding = 'utf-8'
    html_text = connection.text
    parser = BeautifulSoup(html_text, 'html.parser')
    connection.close()
    return parser


def create_json(parser):
    classrooms = [i.text for i in parser.find_all('td', 'R1C2')]
    dates = [i.text[:-1] for i in parser.find_all('td', 'R2C0')] + [
        i.text[:-1] for i in parser.find_all('td', 'R23C0')]

    to_json = {'classrooms': classrooms, 'dates': dates, 'schedule': None}

    tr_list = parser.find_all('tr')[2:-1]
    tr_list = [str(i) for i in tr_list]
    td_list = []
    for i in range(len(tr_list)):
        sub_parser = BeautifulSoup(tr_list[i], 'html.parser')
        tmp = sub_parser.find_all('td')[:-2]
        if len(tmp) == 60:
            tmp = tmp[1:]
        td_list.append(tmp)

    classroom_dict = dict()
    for i in classrooms:
        tmp_dict = dict()
        for j in dates:
            tmp_dict[j] = None
        classroom_dict[i] = tmp_dict
    to_json['schedule'] = classroom_dict

    for i in range(len(classrooms)):
        for j in range(len(dates)):
            result_text = ''
            schedule_day = td_list[j * 7: (j + 1) * 7]
            for k in range(len(schedule_day)):
                result_text += schedule_day[k][0].text + \
                    ' - ' + schedule_day[k][1 + i].text + '\n'
            to_json['schedule'][classrooms[i]][dates[j]] = result_text

    with open(path_to_json, 'a') as file:
        json.dump(to_json, file)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.from_user.id,
                     "Привет! Для получения расписания занятости аудиотрий введи ее номер в формате 14-xxx!")


@bot.message_handler(content_types=['text'])
def choose_date(message):
    global classroom
    markup = types.InlineKeyboardMarkup()
    with open(path_to_json, 'r') as file:
        json_file = json.load(file)
        classrooms = json_file['classrooms']
        dates = json_file['dates']
        if re.fullmatch(r'14-\d{3}', message.text) and message.text in classrooms:
            classroom = message.text
            for i in dates:
                btn = types.InlineKeyboardButton(i, callback_data=i)
                markup.add(btn)
            bot.send_message(message.from_user.id,
                             'Выберите дату: ', reply_markup=markup)
        else:
            bot.send_message(message.from_user.id, "Неверная аудитория!")


@bot.callback_query_handler(func=lambda call: True)
def choose_date(call):
    global classroom
    with open(path_to_json, 'r') as file:
        json_file = json.load(file)
        dates = json_file['dates']
        classrooms = json_file['classrooms']
        schedule = json_file['schedule']
    message = call.data
    if message in dates and classroom in classrooms:
        bot.send_message(call.from_user.id, "Расписание кабинета " + classroom + " в " + message + "\n" +
                         schedule[classroom][message])
    else:
        bot.send_message(call.from_user.id,
                         "Неверная аудитория или расписание!")


if __name__ == '__main__':
    if path.isfile(path_to_json) is False:
        p = connection_for_parsing()
        create_json(p)

    bot.polling(none_stop=True)
