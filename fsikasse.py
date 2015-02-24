#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

# python3 workaround
try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass

from sqlite3 import dbapi2 as sqlite3
import os
import re
import random
import string
from datetime import datetime

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from werkzeug import secure_filename
from PIL import Image
app = Flask(__name__)

# regex to check for valid email adresses
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'kasse.db'),
    UPLOAD_FOLDER = 'static/',
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif']),
    PROFILE_IMAGE_SIZE = (150, 200),
    STORAGE_ACCOUNT = (4, 'Lager/Kühlschrank'),
    CASH_IN_ACCOUNT = (1, 'FSI: Graue Kasse'),
    MONEY_VALUABLE_ID = 1,
    SECRET_KEY='development key',
))

def randomword(length):
   return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def show_index():
    db = get_db()
    db = db.execute(
        'SELECT user.name AS name, image_path, balance FROM user, account_valuable_balance AS avb WHERE active=1 AND browsable=1 AND user.account_id = avb.account_id AND valuable_id = ? ORDER BY balance DESC',
        [app.config['MONEY_VALUABLE_ID']])
    users = db.fetchall()

    return render_template('start.html', title="Benutzerübersicht", users=users)

@app.route('/admin', methods=['GET'])
def admin_index():
    db = get_db()
    db = db.execute(
        'SELECT user.name AS name, image_path, balance FROM user, account_valuable_balance AS avb WHERE active=1 AND browsable=1 AND user.account_id = avb.account_id AND valuable_id = ? ORDER BY balance DESC',
        [app.config['MONEY_VALUABLE_ID']])
    users = db.fetchall()

    return render_template('start.html', title="Benutzerübersicht", admin_panel=True, users=users)

@app.route('/user/<username>')
def show_userpage(username):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'SELECT name, image_path, account_id, direct_payment FROM user WHERE active=1 and name=?',
        [username])
    user = cur.fetchone()
    if not user:
        abort(404)
    cur = db.execute('SELECT name, image_path FROM user WHERE active=1 AND direct_payment=0 AND browsable=1 AND name!=?', [username])
    user_list = cur.fetchall()
    cur = db.execute(
        'SELECT balance FROM account_valuable_balance WHERE account_id=? and valuable_id=?',
        [user['account_id'], app.config['MONEY_VALUABLE_ID']])
    user_balance = cur.fetchone()
    cur = cur.execute('SELECT valuable.name AS name, price, unit_name, symbol, image_path FROM valuable, unit WHERE unit.name = valuable.unit_name AND product = 1')
    products = cur.fetchall()
    return render_template(
        'show_userpage.html', title="Getränkeliste", user=user, products=products, balance=user_balance,
        user_list=user_list)

@app.route('/user/<username>/buy/<valuablename>')
def action_buy(username, valuablename):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'SELECT rowid, name, account_id, direct_payment FROM user WHERE active=1 and name=?',
        [username])
    user = cur.fetchone()
    if not user:
        abort(404)

    cur.execute('SELECT rowid, price FROM valuable WHERE product=1 and name=?', [valuablename])
    valuable = cur.fetchone()
    cur.execute('INSERT INTO `transaction` (datetime) VALUES (?)', [datetime.now()])
    transaction_id = cur.lastrowid
    cur.execute('INSERT INTO transfer (from_id, to_id, valuable_id, amount, transaction_id) VALUES  (?, ?, ?, ?, ?)', [app.config['STORAGE_ACCOUNT'][0], user['account_id'], valuable['rowid'], 1, transaction_id])
    if not user['direct_payment']:
        cur.execute('INSERT INTO transfer (from_id, to_id, valuable_id, amount, transaction_id) VALUES  (?, ?, ?, ?, ?)', [user['account_id'], None, app.config['MONEY_VALUABLE_ID'], valuable['price'], transaction_id])
    else:
        cur.execute('INSERT INTO transfer (from_id, to_id, valuable_id, amount, transaction_id) VALUES  (?, ?, ?, ?, ?)', [None, app.config['CASH_IN_ACCOUNT'][0], app.config['MONEY_VALUABLE_ID'], valuable['price'], transaction_id])
    db.commit()

    if user['direct_payment']:
        flash('Bitte {:.2f} € in die graue Kasse legen.'.format(valuable['price']/100.0))
    else:
        flash('Einkauf war erfolgreich :)')
    return redirect(url_for('show_index'))

@app.route('/user/<username>/transfer', methods=['POST'])
def transfer_money(username):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'SELECT rowid, name, account_id FROM user WHERE active=1 and direct_payment=0 and name=?',
        [username])
    user = cur.fetchone()
    cur.execute(
        'SELECT rowid, name, account_id FROM user WHERE active=1 and direct_payment=0 and name=?',
        [request.form['to']])
    to_user = cur.fetchone()
    if not user or not to_user:
        abort(404)

    amount = int(float(request.form['amount'])*100)

    if amount <= 0.0:
        flash(u'Keine Transaktion durchgeführt.')
        return redirect(url_for('show_index'))

    cur.execute('INSERT INTO `transaction` (datetime) VALUES (?)', [datetime.now()])
    transaction_id = cur.lastrowid
    cur.execute('INSERT INTO transfer (from_id, to_id, valuable_id, amount, transaction_id) VALUES  (?, ?, ?, ?, ?)',
        [user['account_id'], to_user['account_id'], app.config['MONEY_VALUABLE_ID'], amount, transaction_id])
    db.commit()

    flash('Geld wurde überwiesen.')
    return redirect(url_for('show_index'), title="Benutzerübersicht" )

@app.route('/user/<username>/profile', methods=['POST', 'GET'])
def edit_userprofile(username):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        'SELECT name, image_path, account_id, mail, allow_edit_profile FROM user WHERE active=1 AND name=?',
        [username])
    user = cur.fetchone()
    if not user:
        abort(404)

    if request.method == 'GET':
        cur = db.execute(
            'SELECT valuable_name, balance, unit_name FROM account_valuable_balance WHERE account_id=?',
            [user['account_id']])
        balance = cur.fetchall()
        cur = db.execute(
            'SELECT `transaction`.rowid, comment, datetime, account_from.name AS from_name, from_id, account_to.name AS to_name, to_id, amount, valuable.unit_name, valuable.name AS valuable_name, valuable_id FROM `transaction` JOIN transfer ON `transaction`.rowid = transfer.transaction_id JOIN `valuable` ON transfer.valuable_id = valuable.rowid LEFT JOIN account AS account_from ON from_id = account_from.rowid LEFT JOIN account AS account_to ON to_id = account_to.rowid WHERE from_id = ? OR to_id = ?  ORDER BY strftime("%s", datetime) DESC',
            [user['account_id'], user['account_id']])
        transactions = cur.fetchall()
        return render_template('user_profile.html', title="Benutzerprofil " + user['name'], user=user, transactions=transactions, balance=balance, return_to_userpage=True)
    else:  # request.method == 'POST':
        if not user['allow_edit_profile']:
            abort(403)

        if request.form['mail'] == '' or not EMAIL_REGEX.match(request.form['mail']):
            flash(u'Bitte eine korrekte Kontaktadresse angeben, danke!')
            return redirect(url_for('edit_userprofile', username=user['name']))

        cur.execute('UPDATE account SET name=? WHERE rowid = ?',
                   [request.form['name'], user['account_id']])

        filename = user['image_path']
        if request.files['image'] and request.files['image'].filename != '':
            # Replace image
            image = request.files['image']
            assert image and allowed_file(image.filename), \
                "No image given or invalid filename/extension."
            filename = 'users/'+randomword(10)+'_'+secure_filename(image.filename)

            # Resizing image with PIL
            im = Image.open(image)

            # cut/crop image if not 3:4 ratio
            if float(im.size[0]) / float(im.size[1]) > 3.0/4.0: # crop width
                new_width = int(im.size[0] * ( ( float(im.size[1]) * 3.0 )/ ( float(im.size[0]) * 4.0 ) ) )
                left = int(im.size[0]/2 - new_width/2)
                im = im.crop((left, 0, left + new_width, im.size[1]))
                flash(u'Image had to be cropped to 3:4 ratio, sorry!')
	    elif float(im.size[0]) / float(im.size[1]) < 3.0/4.0: # crop height
                new_height = int(im.size[1] * ( ( float(im.size[0]) * 4.0 )/ ( float(im.size[1]) * 3.0 ) ) )
                top = int(im.size[1]/2 - new_height/2)
                im = im.crop((0, top, im.size[0], top + new_height))
                flash(u'Image had to be cropped to 3:4 ratio, sorry!')

            im.thumbnail(app.config['PROFILE_IMAGE_SIZE'], Image.ANTIALIAS)
            im.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cur.execute('UPDATE user SET name=?, mail=?, image_path=? WHERE name=?',
                   [request.form['name'], request.form['mail'], filename, username])
        db.commit()

        if request.files['image'] and user['image_path']:
            # Remove old profile image
            os.unlink(os.path.join(app.config['UPLOAD_FOLDER'], user['image_path']))

        flash(u'Benutzerprofil erfolgreich aktualisiert!')
        return redirect(url_for('edit_userprofile', username=request.form['name']))

@app.route('/user/add', methods=['POST', 'GET'])
def add_user():
    if request.method == 'GET':
        return render_template('add_user.html', title="Benutzer hinzufügen", admin_panel=True)
    else:  # request.method == 'POST'
        db = get_db()
        cur = db.cursor()

        if request.form['name'] == '':
            flash(u'Bitte einen Namen angeben, danke!')
            return redirect(url_for('show_index'))

        if request.form['mail'] == '' or not EMAIL_REGEX.match(request.form['mail']):
            flash(u'Bitte eine Kontaktadresse angeben, danke!')
            return redirect(url_for('show_index'))

        cur.execute('INSERT INTO account (name) VALUES (?)',
                   [request.form['name']])

        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = 'users/'+randomword(10)+'_'+secure_filename(image.filename)

            # Resizing/saving image with PIL
            im = Image.open(image)

            # cut/crop image if not 3:4 ratio
            if float(im.size[0]) / float(im.size[1]) > 3.0/4.0: # crop width
                new_width = int(im.size[0] * ( ( float(im.size[1]) * 3.0 )/ ( float(im.size[0]) * 4.0 ) ) )
                left = int(im.size[0]/2 - new_width/2)
                im = im.crop((left, 0, left + new_width, im.size[1]))
                flash(u'Image had to be cropped to 3:4 ratio, sorry!')
            elif float(im.size[0]) / float(im.size[1]) < 3.0/4.0: # crop height
                new_height = int(im.size[1] * ( ( float(im.size[0]) * 4.0 )/ ( float(im.size[1]) * 3.0 ) ) )
                top = int(im.size[1]/2 - new_height/2)
                im = im.crop((0, top, im.size[0], top + new_height))
                flash(u'Image had to be cropped to 3:4 ratio, sorry!')


            im.thumbnail(app.config['PROFILE_IMAGE_SIZE'], Image.ANTIALIAS)
            im.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None

        cur.execute('INSERT INTO user (name, mail, account_id, image_path) VALUES (?, ?, ?, ?)',
                   [request.form['name'], request.form['mail'], cur.lastrowid, filename])
        db.commit()
        return redirect(url_for('edit_userprofile', username=request.form['name']))

@app.route('/user/<username>/add', methods=['POST'])
def add_to_account(username):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT account_id FROM user WHERE active=1 AND name=? AND direct_payment=0',
        [username])
    user = cur.fetchone()

    if not user:
        abort(404)

    amount = int(float(request.form['amount'])*100)

    if amount <= 0.0:
        flash(u'Keine Transaktion durchgeführt.')
        return redirect(url_for('show_index'))

    cur.execute('INSERT INTO `transaction` (datetime) VALUES (?)', [datetime.now()])
    transaction_id = cur.lastrowid
    cur.execute(
        'INSERT INTO transfer (from_id, to_id, valuable_id, amount, transaction_id) ' +
            'VALUES  (?, ?, ?, ?, ?)',
        [None, user['account_id'], app.config['MONEY_VALUABLE_ID'], amount, transaction_id])
    cur.execute(
        'INSERT INTO transfer (from_id, to_id, valuable_id, amount, transaction_id) ' +
            'VALUES  (?, ?, ?, ?, ?)',
        [None, app.config['CASH_IN_ACCOUNT'][0], app.config['MONEY_VALUABLE_ID'], amount, transaction_id])
    db.commit()
    flash(u'Danke für das Geld :)')

    return redirect(url_for('show_index'))

@app.route('/user/<username>/sub', methods=['POST'])
def sub_from_account(username):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT account_id FROM user WHERE active=1 AND name=? AND direct_payment=0',
        [username])
    user = cur.fetchone()

    if not user:
        abort(404)

    amount = int(float(request.form['amount'])*100)

    if amount <= 0.0:
        flash(u'Keine Transaktion durchgeführt.')
        return redirect(url_for('show_index'))

    cur.execute('INSERT INTO `transaction` (datetime) VALUES (?)', [datetime.now()])
    transaction_id = cur.lastrowid
    cur.execute(
        'INSERT INTO transfer (from_id, to_id, valuable_id, amount, transaction_id) ' +
            'VALUES  (?, ?, ?, ?, ?)',
        [user['account_id'], None, app.config['MONEY_VALUABLE_ID'], amount, transaction_id])
    cur.execute(
        'INSERT INTO transfer (from_id, to_id, valuable_id, amount, transaction_id) ' +
            'VALUES  (?, ?, ?, ?, ?)',
        [app.config['CASH_IN_ACCOUNT'][0], None, app.config['MONEY_VALUABLE_ID'], amount, transaction_id])
    db.commit()
    flash(u'Geld wurde abgezogen.')

    return redirect(url_for('show_index'))

@app.route('/user/<username>/cancel/<int:transaction_id>')
def cancle_transaction(username, transaction_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT account_id FROM user WHERE active=1 AND name=? AND direct_payment=0',
        [username])
    user = cur.fetchone()

    if not user:
        abort(404)

    cur.execute(
        'SELECT from_id, to_id, valuable_id, amount FROM transfer WHERE transaction_id = ?',
        [transaction_id])
    transfers = cur.fetchall()

    cur.execute('INSERT INTO `transaction` (datetime, comment) VALUES (?, ?)',
        [datetime.now(), 'Storno von '+str(transaction_id)+' durch '+username])
    cancle_transaction_id = cur.lastrowid
    for t in transfers:
        cur.execute(
            'INSERT INTO transfer (from_id, to_id, valuable_id, amount, transaction_id) ' +
                'VALUES  (?, ?, ?, ?, ?)',
            [t['to_id'], t['from_id'], t['valuable_id'], t['amount'], cancle_transaction_id])
    db.commit()

    flash('Buchung wurde storniert.')
    return redirect(url_for('edit_userprofile', username=username))

if __name__ == '__main__':
    app.debug = True
    app.run()
