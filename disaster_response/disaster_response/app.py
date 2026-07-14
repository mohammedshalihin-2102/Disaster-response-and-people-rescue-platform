from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "disaster_secret"

DATABASE = "database.db"

# ---------------- DATABASE CONNECTION ----------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- CREATE TABLES ----------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS incident(
        incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
        disaster_type TEXT,
        location TEXT,
        latitude REAL,
        longitude REAL,
        severity INTEGER,
        reported_time DATETIME,
        status TEXT
    )
    ''')


    cur.execute('''
    CREATE TABLE IF NOT EXISTS victim(
        victim_id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id INTEGER,
        name TEXT,
        age INTEGER,
        gender TEXT,
        medical_condition TEXT,
        priority_level INTEGER,
        rescue_status TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS rescue_team(
        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name TEXT,
        availability TEXT,
        skills TEXT,
        equipment TEXT
    )
    ''')

    # ✅ ASSIGNMENT TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS assignment(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id INTEGER,
        team_id INTEGER,
        status TEXT,
        FOREIGN KEY(incident_id) REFERENCES incident(id),
        FOREIGN KEY(team_id) REFERENCES team(id)
    )
    """)

    cur.execute('''
    CREATE TABLE IF NOT EXISTS historical_log(
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id INTEGER,
        action TEXT,
        timestamp DATETIME
    )
    ''')

    conn.commit()
    conn.close()

init_db()


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_db()
        conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                     (username, password, role))
        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?",
                            (username, password)).fetchone()
        conn.close()

        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "Admin":
                return redirect(url_for("admin_dashboard"))
            elif user["role"] == "Team":
                return redirect(url_for("team_dashboard"))
            else:
                return redirect(url_for("citizen_dashboard"))

        flash("Invalid Credentials")

    return render_template("login.html")


@app.route("/admin_dashboard")
def admin_dashboard():
    conn = get_db()
    incidents = conn.execute("SELECT COUNT(*) as total FROM incident").fetchone()
    victims = conn.execute("SELECT COUNT(*) as total FROM victim").fetchone()
    teams = conn.execute("SELECT COUNT(*) as total FROM rescue_team").fetchone()
    conn.close()

    return render_template("admin_dashboard.html",
                           incidents=incidents["total"],
                           victims=victims["total"],
                           teams=teams["total"])

# ---------------- VIEW INCIDENTS ----------------
@app.route("/incidents")
def incidents():
    conn = get_db()
    data = conn.execute("SELECT * FROM incident").fetchall()
    conn.close()
    return render_template("incidents.html", data=data)


# ---------------- ADD INCIDENT ----------------
@app.route("/add_incident", methods=["POST"])
def add_incident():
    conn = get_db()

    conn.execute('''
        INSERT INTO incident(disaster_type, location, latitude, longitude, severity, reported_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        request.form["disaster_type"],
        request.form["location"],
        request.form["latitude"],
        request.form["longitude"],
        request.form["severity"],
        datetime.now(),
        "Active"
    ))

    conn.commit()
    conn.close()
    return redirect(url_for("incidents"))


# ---------------- DELETE INCIDENT ----------------
@app.route("/delete_incident/<int:id>")
def delete_incident(id):
    conn = get_db()
    conn.execute("DELETE FROM incident WHERE incident_id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("incidents"))


# ---------------- UPDATE INCIDENT STATUS ----------------
@app.route("/update_incident/<int:id>", methods=["POST"])
def update_incident(id):
    conn = get_db()
    conn.execute("UPDATE incident SET status=? WHERE incident_id=?",
                 (request.form["status"], id))
    conn.commit()
    conn.close()
    return redirect(url_for("incidents"))





@app.route("/victims", methods=["GET","POST"])
def victims():
    conn = get_db()

    if request.method == "POST":
        conn.execute('''
        INSERT INTO victim(incident_id,name,age,gender,medical_condition,priority_level,rescue_status)
        VALUES (?,?,?,?,?,?,?)
        ''', (
            request.form["incident_id"],
            request.form["name"],
            request.form["age"],
            request.form["gender"],
            request.form["medical_condition"],
            request.form["priority_level"],
            "Pending"
        ))
        conn.commit()

    victims = conn.execute("SELECT * FROM victim").fetchall()
    conn.close()
    return render_template("victims.html", victims=victims)
@app.route("/delete_victim/<int:id>")
def delete_victim(id):
    conn = get_db()
    conn.execute("DELETE FROM victim WHERE victim_id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("victims"))
# ---------------- VIEW + ADD TEAM ----------------
@app.route("/teams", methods=["GET", "POST"])
def teams():
    conn = get_db()

    if request.method == "POST":
        conn.execute('''
            INSERT INTO rescue_team(team_name, availability, skills, equipment)
            VALUES (?, ?, ?, ?)
        ''', (
            request.form["team_name"],
            "Available",
            request.form["skills"],
            request.form["equipment"]
        ))
        conn.commit()

    teams = conn.execute("SELECT * FROM rescue_team").fetchall()
    conn.close()
    return render_template("teams.html", teams=teams)


# ---------------- DELETE TEAM ----------------
@app.route("/delete_team/<int:id>")
def delete_team(id):
    conn = get_db()
    conn.execute("DELETE FROM rescue_team WHERE team_id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("teams"))


# ---------------- EDIT TEAM PAGE ----------------
@app.route("/edit_team/<int:id>")
def edit_team(id):
    conn = get_db()
    team = conn.execute("SELECT * FROM rescue_team WHERE team_id=?", (id,)).fetchone()
    conn.close()
    return render_template("edit_team.html", team=team)


# ---------------- UPDATE TEAM ----------------
@app.route("/update_team/<int:id>", methods=["POST"])
def update_team(id):
    conn = get_db()
    conn.execute('''
        UPDATE rescue_team
        SET team_name=?, availability=?, skills=?, equipment=?
        WHERE team_id=?
    ''', (
        request.form["team_name"],
        request.form["availability"],
        request.form["skills"],
        request.form["equipment"],
        id
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("teams"))

@app.route("/team_dashboard")
def team_dashboard():
    conn = get_db()
    assignments = conn.execute("SELECT * FROM assignment WHERE status='In-progress'").fetchall()
    conn.close()
    return render_template("team_dashboard.html", assignments=assignments)
@app.route("/reports")
def reports():
    conn = get_db()

    active = conn.execute("SELECT COUNT(*) as total FROM incident WHERE status='Active'").fetchone()
    resolved = conn.execute("SELECT COUNT(*) as total FROM incident WHERE status='Resolved'").fetchone()

    conn.close()

    return render_template("reports.html",
                           active=active["total"],
                           resolved=resolved["total"])
@app.route('/assignments')
def assignments():
    conn = sqlite3.connect('drpr.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT assignment.id, incident.location, team.team_name, assignment.status
    FROM assignment
    JOIN incident ON assignment.incident_id = incident.id
    JOIN team ON assignment.team_id = team.id
    """)
    data = cursor.fetchall()
    conn.close()

    return render_template('assignments.html', assignments=data)
@app.route('/add_assignment', methods=['POST'])
def add_assignment():
    incident_id = request.form['incident_id']
    team_id = request.form['team_id']
    status = request.form['status']

    conn = sqlite3.connect('drpr.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO assignment (incident_id, team_id, status) VALUES (?, ?, ?)",
                   (incident_id, team_id, status))
    conn.commit()
    conn.close()

    return redirect('/assignments')
@app.route('/delete_assignment/<int:id>')
def delete_assignment(id):
    conn = sqlite3.connect('drpr.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM assignment WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/assignments')
@app.route('/update_assignment/<int:id>', methods=['POST'])
def update_assignment(id):
    status = request.form['status']

    conn = sqlite3.connect('drpr.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE assignment SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()

    return redirect('/assignments')

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)

