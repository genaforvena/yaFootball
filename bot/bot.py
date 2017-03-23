import logging
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

import sqlite3

DATABASE = "../yaFootball.db"

TOKEN = "357076937:AAGMTWhLSqR31XcCvGTkqbx_I3tCaXQ1KVM"

updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

def execute(statement):
    rv = sqlite3.connect(DATABASE)
    rv.row_factory = sqlite3.Row
    rv.execute(statement)
    rv.commit()
    rv.close()


def start(bot, update):
    id = update.message.chat_id
    telegram_handler = update.message.from_user.username
    execute("INSERT INTO players (id, telegram_handler) values ({}, '{}')".format(id, telegram_handler))
    bot.sendMessage(chat_id=id, text=str(id) + " with telegram handler: " + telegram_handler + " was added into db!")

def echo(bot, update):
    bot.sendMessage(chat_id=player_id, text=player_id + " was added into db!")



start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()
