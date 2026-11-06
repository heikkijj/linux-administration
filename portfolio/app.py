from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)


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

def record_visit():
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
    return render_template('week2.html', title='Week 2', visits=visits)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)