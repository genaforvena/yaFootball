import logging
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

import sqlite3

DATABASE = "../yaFootball.db"

TOKEN = "357076937:AAGMTWhLSqR31XcCvGTkqbx_I3tCaXQ1KVM"

updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

def get_db():
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row
    return rv


def execute(statement):
    rv = get_db()
    rv.execute(statement)
    rv.commit()
    rv.close()


def extract_arguments(update):
    return ' '.join(update.message.text.split(' ')[1:])

def get_id(update):
    return update.message.chat_id

def set_name(bot, update):
    id = get_id(update)
    name = extract_arguments(update)
    execute("UPDATE players SET name = '{}' WHERE id = {}".format(name, id))
    update.message.reply_text("Name set to " + name)


def set_ya_handler(bot, update):
    id = get_id(update)
    ya_handler = extract_arguments(update)
    execute("UPDATE players SET ya_handler = '{}' WHERE id = {}".format(ya_handler, id))
    update.message.reply_text("ya_handler set to " + ya_handler)


def show_player_info(bot, update):
    id = get_id(update)
    db = get_db()
    cursor = db.execute("SELECT * FROM players WHERE id = {}".format(id))
    result = cursor.fetchall()
    db.close()

    result_info = [dict(x) for x in result][0]
    update.message.reply_text("Player info: " + str(result_info))


def start(bot, update):
    id = get_id(update)
    telegram_handler = update.message.from_user.username
    execute("INSERT INTO players (id, telegram_handler) values ({}, '{}')".format(id, telegram_handler))
    update.message.reply_text(str(id) + " with telegram handler: " + telegram_handler + " was added into db!")


def main():
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    set_name_handler = CommandHandler('set_name', set_name)
    dispatcher.add_handler(set_name_handler)

    set_ya_handler_handler = CommandHandler('set_ya_handler', set_ya_handler)
    dispatcher.add_handler(set_ya_handler_handler)

    show_player_info_handler = CommandHandler("info", show_player_info)
    dispatcher.add_handler(show_player_info_handler)

    # echo_handler = MessageHandler(Filters.text, echo)
    # dispatcher.add_handler(echo_handler)

    updater.start_polling()

if __name__ == "__main__":
    main()
