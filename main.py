import telebot
import requests
import json
import redis
from pathlib import Path
import datetime


file = Path('config.json')
config = json.loads(file.read_text())
help = Path('help.txt')

bot = telebot.TeleBot(config['token'])
r = redis.Redis(host=config['database']['url'], port=config['database']['port'], db=0)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    res = f'Hello, {message.from_user.first_name}\n'
    res += help.read_text()
    bot.reply_to(message, res)

@bot.message_handler(commands=['list', 'lst'])
def send_list(message):
    id_user = message.from_user.id
    time_last_requests = datetime.datetime.now() - r.lastsave()
    recom_diff = datetime.timedelta(minutes=10)
    list = ''

    if time_last_requests > recom_diff:
        get_response = requests.get(config['url'] + 'latest?base=USD').json()
        for currency, value in get_response['rates'].items():
            list += f'{currency}: {round(value, 2)}\n'

        r.set(id_user, list)
    else:
        print(time_last_requests)
        list = r.get(id_user).decode()

    bot.reply_to(message, list)

@bot.message_handler(commands=['exchange'])
def send_exchange(message):
    element_message = message.text.split(' ')
    res = ''
    if len(element_message) == 4 and element_message[1][0] == '$':
        get_response = requests.get(config['url'] + f'latest?base=USD&symbols={element_message[3]}').json()
        value = int(element_message[1][1:])
        dol_to_currency = get_response['rates'][element_message[3]]
        res += element_message[3] + ' ' + str(round(value * dol_to_currency, 2))
    elif len(element_message) == 5:
        get_response = requests.get(config['url'] + f'latest?base={element_message[2]}&symbols={element_message[4]}').json()
        value = int(element_message[1])
        dol_to_currency = get_response['rates'][element_message[4]]
        res += element_message[4] + ' ' + str(round(value * dol_to_currency, 2))
    else:
        res = f'Please, command format:\n /exchange $10 to CAD \n or \n /exchange 10 USD to CAD'
    bot.reply_to(message, res)


bot.polling(none_stop=True)