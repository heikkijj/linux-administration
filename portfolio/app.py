from flask import Flask, make_response, render_template, send_from_directory
import pymysql
import sqlite3
import os

app = Flask(__name__)

COUNTER_BACKEND = os.environ.get('COUNTER_BACKEND', 'sqlite')
COUNTER_ROLE = os.environ.get('COUNTER_ROLE', 'source')
if COUNTER_BACKEND not in ('sqlite', 'mariadb'):
    raise ValueError('COUNTER_BACKEND must be sqlite or mariadb')
if COUNTER_ROLE not in ('source', 'replica'):
    raise ValueError('COUNTER_ROLE must be source or replica')
if COUNTER_ROLE == 'replica' and COUNTER_BACKEND != 'mariadb':
    raise ValueError('The replica requires the MariaDB backend')
DB_CONFIG = os.environ.get('COUNTER_DB_CONFIG')
if COUNTER_BACKEND == 'mariadb' and not DB_CONFIG:
    raise ValueError('COUNTER_DB_CONFIG is required for MariaDB')

# Keep the database and HTML alongside this application.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, 'counter.db')
def init_db():
    # Initialize database if thats not alredy done. #
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visits INTEGER NOT NULL
        )
    ''')
    # check table have starting row.
    # If not insert initial row with 0 visits.
    cursor.execute('SELECT COUNT(*) FROM stats')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO stats (visits) VALUES (0)')
    conn.commit()
    conn.close()

def mariadb_counter(increment=False):
    conn = pymysql.connect(
        read_default_file=DB_CONFIG,
        unix_socket='/run/mysqld/mysqld.sock',
        database='portfilio_db',
    )
    try:
        with conn.cursor() as cursor:
            if increment:
                cursor.execute('UPDATE visitor_counter SET count = count + 1 WHERE id = 1')
                if cursor.rowcount != 1:
                    raise RuntimeError('MariaDB visitor counter row is missing')
            cursor.execute('SELECT count FROM visitor_counter WHERE id = 1')
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError('MariaDB visitor counter row is missing')
        conn.commit()
        return row[0]
    finally:
        conn.close()


def record_visit():
    if COUNTER_BACKEND == 'mariadb':
        return mariadb_counter(increment=COUNTER_ROLE == 'source')
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('UPDATE stats SET visits = visits + 1 WHERE id = 1')
        return conn.execute('SELECT visits FROM stats WHERE id = 1').fetchone()[0]


# Flask routes for the web application all pages.
@app.route('/')
def index():
    record_visit()
    return render_template('index.html', title='Home')


@app.route('/week1/')
def week1():
    record_visit()
    return render_template('week1.html', title='Week 1')


@app.route('/week2/')
def week2():
    visits = record_visit()
    return render_template('week2.html', title='Week 2', visits=visits,
                           counter_backend=COUNTER_BACKEND, counter_role=COUNTER_ROLE)

@app.route('/week3/')
def week3():
    record_visit()
    return render_template('week3.html', title='Week 3')


@app.route('/week4/')
@app.route('/viikko4/')
def week4():
    visits = mariadb_counter() if COUNTER_ROLE == 'replica' else None
    response = make_response(render_template('week4.html', title='Week 4', visits=visits))
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.route('/week3/status-report/')
def week3_status_report():
    response = make_response(
        send_from_directory(os.path.join(APP_DIR, 'static'), 'status-report.html')
    )
    response.headers['Cache-Control'] = 'no-store'
    return response


if __name__ == '__main__':
    if COUNTER_BACKEND == 'sqlite':
        init_db()
    app.run(host='127.0.0.1', port=5000)