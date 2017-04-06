#!server/bin/python
# -*- coding: utf-8 -*-
import json
import sqlite3
import os
import sys
import telegram

from bot.bot import match_to_str, players_to_str, match_and_players_to_str, \
    select_players_in_match, boot, bot, dispatcher

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify
from flask_sslify import SSLify

DATABASE = '/home/yafootball/yaFootball/yaFootball/yaFootball.db'

app = Flask(__name__)
sslify = SSLify(app)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, DATABASE),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config['JSON_AS_ASCII'] = False
app.config.from_envvar('YA_FOOTBALL_SETTINGS', silent=True)


@app.cli.command('initdb')
def initdb_command():
    print('Starting db init')
    init_db()
    print('Initialized the database.')

@app.cli.command('start_bot')
def start_bot():
    print("starting bot")
    boot()
    print("bot was started")


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/bot', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(), bot)
        dispatcher.process_update(update)
    return "ok"


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/notify', methods=['POST'])
def notify():
    if not session.get('logged_in'):
        abort(401)
    notify_players()
    return redirect(url_for('show_entries'))


@app.route('/notify_all', methods=['POST'])
def notify_all():
    if not session.get('logged_in'):
        abort(401)
    notify_everyone()
    return redirect(url_for('show_entries'))


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('INSERT INTO matches (players_limit, place, time) values (?, ?, ?)',
                [request.form["players_limit"],
                request.form["place"],
                request.form["time"]])
    db.commit()
    notify_everyone()
    return redirect(url_for('show_entries'))


@app.route('/add_match')
def add_match():
    if not session.get('logged_in'):
        abort(401)
    return render_template('add_match.html')


@app.route('/')
def show_entries():
    db = get_db()
    next_match = select_next_match(db)
    next_match_id = next_match['id']
    result = db.execute('select * from players join players_in_match on players.id = players_in_match.player_id where match_id = {};'.format(next_match_id))
    entries = result.fetchall()
    for i, entry in enumerate(entries):
        entry["index"] = i + 1
    return render_template('show_entries.html', entries=entries, match=next_match)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


def notify_everyone():
    db = get_db()
    next_match = select_next_match(db)
    players = db.execute('select * from players').fetchall()
    for player in players:
        try:
            bot.sendMessage(chat_id=player['id'], text="Следующий матч\n" + match_to_str(next_match))
        except:
            print("Unexpected error:", sys.exc_info()[0])


def notify_players():
    db = get_db()
    next_match = select_next_match(db)
    players_in_match = select_players_in_match(db, match_id=next_match["id"])
    for player in players_in_match:
        try:
            bot.sendMessage(chat_id=player['player_id'], text="Играем!\n" + match_to_str(next_match))
        except:
            print("Unexpected error:", sys.exc_info()[0])


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = make_dicts
    return rv


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def select_next_match(db):
    return db.execute('select * from matches order by id desc limit 1').fetchall()[0]


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


if __name__ == '__main__':
    boot()
    app.run(debug=True)
