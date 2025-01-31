import random
import uuid
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)
db_path = 'draw_results.db'

# Katılımcı sözlüğü, isim ve referans numarasını tutacak şekilde güncellendi
participants = {}

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results 
                 (id INTEGER PRIMARY KEY, 
                  winner TEXT, 
                  ref_number TEXT, 
                  date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS monthly_competitions
                 (id INTEGER PRIMARY KEY, 
                  team_name TEXT, 
                  task TEXT, 
                  completion_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS raffles
                 (id INTEGER PRIMARY KEY, 
                  name TEXT, 
                  draw_date TEXT)''')
    conn.commit()
    conn.close()

def add_winner(winner, ref_number, date):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO results (winner, ref_number, date) VALUES (?, ?, ?)', 
              (winner, ref_number, date))
    conn.commit()
    conn.close()

def save_competition(team_name, task, completion_date):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO monthly_competitions (team_name, task, completion_date) VALUES (?, ?, ?)', 
              (team_name, task, completion_date))
    conn.commit()
    conn.close()

def get_previous_results():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT id, winner, ref_number, date FROM results')
    results = c.fetchall()
    conn.close()
    return results

def get_monthly_competitions():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT id, team_name, task, completion_date FROM monthly_competitions')
    results = c.fetchall()
    conn.close()
    return results

def remove_competition(id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('DELETE FROM monthly_competitions WHERE id = ?', (id,))
    conn.commit()
    conn.close()

def remove_winner(id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('DELETE FROM results WHERE id = ?', (id,))
    conn.commit()
    conn.close()

def create_new_raffle(name, draw_date):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO raffles (name, draw_date) VALUES (?, ?)', (name, draw_date))
    conn.commit()
    conn.close()

def get_raffles():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT id, name, draw_date FROM raffles')
    raffles = c.fetchall()
    conn.close()
    return raffles

# Ana sayfa
@app.route('/')
def index():
    last_draw = get_previous_results()[-1] if get_previous_results() else None
    return render_template('index.html', last_draw=last_draw)

# Kayıt olma sayfası
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        if name in participants:
            message = f"{name}, you are already registered! Your Reference Number: {participants[name]}"
        else:
            ref_number = str(uuid.uuid4())[:8]  # Generate a unique reference number
            participants[name] = ref_number
            message = f"Registration successful! Your Reference Number: {ref_number}"
        return render_template('signup.html', message=message)
    return render_template('signup.html', message="")

# Çekiliş sayfası
@app.route('/draw', methods=['POST'])
def draw():
    if participants:
        two_weeks_ago = datetime.now() - timedelta(weeks=2)
        eligible_participants = [name for name in participants if not any(
            result[1] == name and datetime.strptime(result[3], "%Y-%m-%d %H:%M:%S") > two_weeks_ago
            for result in get_previous_results()
        )]

        if eligible_participants:
            winner = random.choice(eligible_participants)
            winner_ref = participants[winner]
            draw_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            add_winner(winner, winner_ref, draw_date)
            winner_info = f"Winner: {winner} (Reference Number: {winner_ref}), Date: {draw_date}"
        else:
            winner_info = "No one is eligible within the last 2 weeks"
    else:
        winner_info = "No participants"

    winners = get_previous_results()
    competitions = get_monthly_competitions()
    return render_template('admin.html', winner_info=winner_info, winners=winners, monthly_competitions=competitions)

# Aylık görev sayfası
@app.route('/monthly_competitions', methods=['GET', 'POST'])
def monthly_competitions():
    if request.method == 'POST':
        team_name = request.form['team_name']
        task = request.form['task']
        completion_date = request.form['completion_date']
        save_competition(team_name, task, completion_date)
        message = f"Task for team {team_name} has been added!"
        competitions = get_monthly_competitions()
        return render_template('monthly_competitions.html', message=message, monthly_competitions=competitions)
    else:
        competitions = get_monthly_competitions()
        return render_template('monthly_competitions.html', monthly_competitions=competitions)

@app.route('/remove_monthly_competition', methods=['POST'])
def remove_monthly_competition():
    id = request.form['id']
    remove_competition(id)
    message = f"Competition record with ID {id} has been removed!"
    competitions = get_monthly_competitions()
    return render_template('monthly_competitions.html', message=message, monthly_competitions=competitions)

@app.route('/remove_winner', methods=['POST'])
def remove_winner_route():
    id = request.form['id']
    remove_winner(id)
    message = f"Raffle record with ID {id} has been removed!"
    winners = get_previous_results()
    competitions = get_monthly_competitions()
    return render_template('admin.html', message=message, winners=winners, monthly_competitions=competitions)

# Admin sayfası
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        raffle_name = request.form['raffle_name']
        draw_date = request.form['draw_date']
        create_new_raffle(raffle_name, draw_date)
        message = f"New raffle {raffle_name} has been created!"
    else:
        message = None
    winners = get_previous_results()
    competitions = get_monthly_competitions()
    raffles = get_raffles()
    return render_template('admin.html', winners=winners, monthly_competitions=competitions, raffles=raffles, message=message)

# Önceki sonuçlar sayfası
@app.route('/previousresults')
def previousresults():
    draw_results = get_previous_results()
    monthly_results = get_monthly_competitions()
    return render_template('previousresults.html', draw_results=draw_results, monthly_results=monthly_results)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
