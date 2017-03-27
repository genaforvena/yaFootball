#!server/bin/python
import json
import sqlite3
import os

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify

DATABASE = 'yaFootball.db'

app = Flask(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, DATABASE),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config['JSON_AS_ASCII'] = False
app.config.from_envvar('YA_FOOTBALL_SETTINGS', silent=True)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = make_dicts
    return rv


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    print('Starting db init')
    init_db()
    print('Initialized the database.')


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


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
    return redirect(url_for('show_entries'))


@app.route('/add_match')
def add_match():
    if not session.get('logged_in'):
        abort(401)
    return render_template('add_match.html')


@app.route('/')
def show_entries():
    db = get_db()
    next_match = db.execute('select * from matches order by id desc limit 1').fetchall()[0]
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


if __name__ == '__main__':
    app.run(debug=True)
