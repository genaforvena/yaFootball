# -*- coding: utf-8 -*-
import logging
import sys
from telegram import Bot
from telegram.ext import Dispatcher
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

import sqlite3

DATABASE = "../yaFootball.db"

TOKEN = "357076937:AAGMTWhLSqR31XcCvGTkqbx_I3tCaXQ1KVM"

reload(sys)
sys.setdefaultencoding('utf8')


def get_db():
    rv = sqlite3.connect(DATABASE)

    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    rv.row_factory = dict_factory
    return rv


def execute(statement):
    rv = get_db()
    rv.execute(statement)
    rv.commit()
    rv.close()


def execute_for_result(statement):
    db = get_db()
    cursor = db.execute(statement)
    result = cursor.fetchall()
    db.close()
    return result


def select_next_match():
    return execute_for_result('select * from matches order by id desc limit 1')[0]


def extract_arguments(update):
    return ' '.join(update.message.text.split(' ')[1:])


def get_id(update):
    return update.message.chat_id


def add_player(bot, update):
    if not check_name_or_handler_set(bot, update):
        return
    player_id = get_id(update)
    match = select_next_match()
    match_id = match['id']

    players = select_players_in_match(match_id)
    players_ids = [x['player_id'] for x in players]

    if player_id in players_ids:
        update.message.reply_text("Ты уже был записан")
        players_in_match_info(bot, update)
        return
    execute("insert into players_in_match (player_id, match_id) values ({}, {})".format(player_id, match_id))

    if len(players) + 1 > match["players_limit"]:
        update.message.reply_text("Тебя посчитали, но пока нет мест. Мы тебе напишем, если освободится место")
    else:
        update.message.reply_text("Записали тебя")

    # Refetch it once again. It's only a bot!
    players = select_players_in_match(match_id)
    if len(players) == match["players_limit"]:
        for player in players:
            bot.send_message(player["player_id"], "Набрались! Матч точно будет! \n" + match_to_str(match))
    else:
        players_in_match_info(bot, update)


def select_players_in_match(match_id):
    return execute_for_result('select * from players_in_match where match_id = {}'.format(match_id))


def remove_player(bot, update):
    player_id = get_id(update)
    match = select_next_match()
    match_id = match['id']

    player_in_match = execute_for_result('select * from players_in_match where match_id = {} and player_id = {}'.format(match_id, player_id))
    if not player_in_match:
        update.message.reply_text('Ты и так не был записан')
        return

    execute("delete from players_in_match where (player_id = {} and match_id = {})".format(player_id, match_id))

    players_in_match = select_players_in_match(match_id)
    players_limit = match["players_limit"]
    if len(players_in_match) >= players_limit:
        player_id_from_waiting_list = players_in_match[players_limit]["player_id"]
        bot.send_message(player_id_from_waiting_list, "Освободилось место! Мы тебя ждем!")
        players_in_match_info(bot, update)

    update.message.reply_text("Жаль ((")


def players_in_match_info(bot, update):
    match = select_next_match()
    next_match_id = match['id']
    result = execute_for_result('select * from players join players_in_match on players.id = players_in_match.player_id where match_id = {};'.format(next_match_id))

    update.message.reply_text(match_and_players_to_str(match, result))

def match_and_players_to_str(match, players):
    return match_to_str(match) + "\n\nИдут: \n" + players_to_str(players)

def players_to_str(players):
    result = ""
    for i, player in enumerate(players):
        result = result + str(i + 1) + ") " + player["name"]
        result = result + "\n"
    return result

def match_to_str(match):
    return "Время: {} \nМесто: {}\nВсего мест: {}".format(match['time'], match['place'], match['players_limit'])


def set_name(bot, update):
    id = get_id(update)
    name = extract_arguments(update)
    if not name:
        update.message.reply_text("""Please provide name. Example:
                                    /set_name Petya Pupkin""")
        return
    execute("UPDATE players SET name = '{}' WHERE id = {}".format(name, id))
    update.message.reply_text("Теперь мы будем называть тебя " + name)
    help(bot, update)

def help(bot, update):
    id = get_id(update)
    update.message.reply_text("/when - когда матч и кто идет\n/add - записаться на следующий матч\n/remove - удалиться из матча\n/set_name - сменить имя в боте")

def error(bot, update):
    id = get_id(update)
    update.message.reply_text("Эта команда мне неизвестна")
    help(bot, update)


def set_ya_handler(bot, update):
    id = get_id(update)
    ya_handler = extract_arguments(update)
    if not ya_handler:
        update.message.reply_text("""Please provide ya_handler. Example:
                                    /set_ya_handler @losin""")
        return
    execute("UPDATE players SET ya_handler = '{}' WHERE id = {}".format(ya_handler, id))
    update.message.reply_text("Твой яндекс логин: " + ya_handler)


def show_player_info(bot, update):
    id = get_id(update)
    result = execute_for_result("SELECT * FROM players WHERE id = {}".format(id))
    update.message.reply_text("Выборка из бд о тебе: " + str(result[0]))


def start(bot, update):
    id = get_id(update)
    if select_players_by_id(id):
        update.message.reply_text("Ты уже зарегистрирован в боте")
        return
    telegram_handler = update.message.from_user.username
    execute("INSERT INTO players (id, telegram_handler) values ({}, '{}')".format(id, telegram_handler))
    update.message.reply_text("Зарегистирировали. Теперь нужно задать имя с помощью команды /set_name\nНапример:\n/set_name Джон До")


def select_player(id):
    return select_players_by_id(id)[0]

def select_players_by_id(id):
    return execute_for_result("select * from players where id = {}".format(id))

def check_name_or_handler_set(bot, update):
    id = get_id(update)
    player = select_player(id)
    if not player['name'] and not player['ya_handler']:
        update.message.reply_text("Нельзя добавляться без заданного имени! \nЗадать имя с помощью команды /set_name\nНапример:\n/set_name Джон До")
        return False
    return True


bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

set_name_handler = CommandHandler('set_name', set_name)
dispatcher.add_handler(set_name_handler)

set_ya_handler_handler = CommandHandler('set_ya_handler', set_ya_handler)
dispatcher.add_handler(set_ya_handler_handler)

show_player_info_handler = CommandHandler('info', show_player_info)
dispatcher.add_handler(show_player_info_handler)

get_closest_match_handler = CommandHandler('when', players_in_match_info)
dispatcher.add_handler(get_closest_match_handler)

add_player_handler = CommandHandler('add', add_player)
dispatcher.add_handler(add_player_handler)

remove_player_handler = CommandHandler('remove', remove_player)
dispatcher.add_handler(remove_player_handler)

get_players_in_match_handler = CommandHandler('players', players_in_match_info)
dispatcher.add_handler(get_players_in_match_handler)

help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)

dispatcher.add_error_handler(error)

bot.setWebhook('https://yafootball.pythonanywhere.com/bot')
