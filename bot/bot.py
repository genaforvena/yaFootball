import logging
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

import sqlite3

DATABASE = "../server/yaFootball/yaFootball.db"

TOKEN = "357076937:AAGMTWhLSqR31XcCvGTkqbx_I3tCaXQ1KVM"

updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher



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


def get_closest_match(bot, update):
    id = get_id(update)
    result = select_next_match()
    update.message.reply_text("Next match is " + str(result[0]))


def add_player(bot, update):
    if not check_name_or_handler_set(bot, update):
        return
    player_id = get_id(update)
    match_id = select_next_match()['id']
    execute("insert into players_in_match (player_id, match_id) values ({}, {})".format(player_id, match_id))
    update.message.reply_text("You was added to the next match!")


def remove_player(bot, update):
    player_id = get_id(update)
    match_id = select_next_match()['id']
    execute("delete from players_in_match where (player_id = {} and match_id = {})".format(player_id, match_id))
    update.message.reply_text("You was removed from match!")


def players_in_match_info(bot, update):
    next_match_id = select_next_match()['id']
    result = execute_for_result('select * from players join players_in_match on players.id = players_in_match.player_id where match_id = {};'.format(next_match_id))
    update.message.reply_text("Result " + str(result))


def set_name(bot, update):
    id = get_id(update)
    name = extract_arguments(update)
    if not name:
        update.message.reply_text("""Please provide name. Example:
                                    /set_name Petya Pupkin""")
        return
    execute("UPDATE players SET name = '{}' WHERE id = {}".format(name, id))
    update.message.reply_text("Name set to " + name)


def set_ya_handler(bot, update):
    id = get_id(update)
    ya_handler = extract_arguments(update)
    if not ya_handler:
        update.message.reply_text("""Please provide ya_handler. Example:
                                    /set_ya_handler @losin""")
        return
    execute("UPDATE players SET ya_handler = '{}' WHERE id = {}".format(ya_handler, id))
    update.message.reply_text("ya_handler set to " + ya_handler)


def show_player_info(bot, update):
    id = get_id(update)
    result = execute_for_result("SELECT * FROM players WHERE id = {}".format(id))
    update.message.reply_text("Player info: " + str(result[0]))


def start(bot, update):
    id = get_id(update)
    telegram_handler = update.message.from_user.username
    execute("INSERT INTO players (id, telegram_handler) values ({}, '{}')".format(id, telegram_handler))
    update.message.reply_text(str(id) + " with telegram handler: " + telegram_handler + " was added into db!")


def select_player(id):
    return execute_for_result("select * from players where id = {}".format(id))[0]


def check_name_or_handler_set(bot, update):
    id = get_id(update)
    player = select_player(id)
    if not player['name'] and not player['ya_handler']:
        update.message.reply_text("""Please set name or ya_hadnler using commands /set_name your_name
                                     or /set_ya_handler your_yandex_handler""")
        return False
    return True


def main():
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    set_name_handler = CommandHandler('set_name', set_name)
    dispatcher.add_handler(set_name_handler)

    set_ya_handler_handler = CommandHandler('set_ya_handler', set_ya_handler)
    dispatcher.add_handler(set_ya_handler_handler)

    show_player_info_handler = CommandHandler('info', show_player_info)
    dispatcher.add_handler(show_player_info_handler)

    get_closest_match_handler = CommandHandler('when', get_closest_match)
    dispatcher.add_handler(get_closest_match_handler)

    add_player_handler = CommandHandler('add', add_player)
    dispatcher.add_handler(add_player_handler)

    remove_player_handler = CommandHandler('remove', remove_player)
    dispatcher.add_handler(remove_player_handler)

    get_players_in_match_handler = CommandHandler('players', players_in_match_info)
    dispatcher.add_handler(get_players_in_match_handler)


    # echo_handler = MessageHandler(Filters.text, echo)
    # dispatcher.add_handler(echo_handler)

    updater.start_polling()

if __name__ == "__main__":
    main()
