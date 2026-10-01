from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secretkey"

DATABASE = "database.db"

# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS teachers(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    subject TEXT,
                    password TEXT
                )''')

    # ✅ UPDATED (added roll_no)
    c.execute('''CREATE TABLE IF NOT EXISTS students(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    roll_no TEXT UNIQUE,
                    password TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS exams(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_name TEXT,
                    subject TEXT,
                    question TEXT,
                    option1 TEXT,
                    option2 TEXT,
                    option3 TEXT,
                    option4 TEXT,
                    answer TEXT
                )''')

    # ✅ UPDATED (added roll_no, mobile_warnings, eye_warnings)
    c.execute('''CREATE TABLE IF NOT EXISTS results(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT,
                    roll_no TEXT,
                    teacher_name TEXT,
                    subject TEXT,
                    score INTEGER,
                    warnings INTEGER,
                    mobile_warnings INTEGER DEFAULT 0,
                    eye_warnings INTEGER DEFAULT 0
                )''')

    # Safe schema migration for existing databases
    c.execute("PRAGMA table_info(results)")
    columns = [col[1] for col in c.fetchall()]
    if "mobile_warnings" not in columns:
        c.execute("ALTER TABLE results ADD COLUMN mobile_warnings INTEGER DEFAULT 0")
    if "eye_warnings" not in columns:
        c.execute("ALTER TABLE results ADD COLUMN eye_warnings INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================

@app.route("/")
def index():
    return render_template("index.html")

# ================= TEACHER LOGIN =================

@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    if request.method == "POST":
        name = request.form["name"]
        subject = request.form["subject"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("SELECT * FROM teachers WHERE name = ?", (name,))
        teacher = c.fetchone()

        if teacher:
            if check_password_hash(teacher[3], password):
                session["teacher_name"] = name
                session["subject"] = teacher[2]
                conn.close()
                return redirect("/teacher_dashboard")
            else:
                conn.close()
                return "Invalid Password"
        else:
            hashed_password = generate_password_hash(password)
            c.execute("INSERT INTO teachers(name, subject, password) VALUES (?,?,?)",
                      (name, subject, hashed_password))
            conn.commit()
            conn.close()

            session["teacher_name"] = name
            session["subject"] = subject
            return redirect("/teacher_dashboard")

    return render_template("teacher_login.html")

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= TEACHER DASHBOARD =================

@app.route("/teacher_dashboard")
def teacher_dashboard():
    if "teacher_name" not in session:
        return redirect("/teacher")
    return render_template("teacher_dashboard.html")

@app.route("/add_exam", methods=["GET", "POST"])
def add_exam():
    if "teacher_name" not in session:
        return redirect("/teacher")

    if request.method == "POST":
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("""INSERT INTO exams(teacher_name, subject, question,
                    option1, option2, option3, option4, answer)
                    VALUES (?,?,?,?,?,?,?,?)""",
                  (session["teacher_name"],
                   session["subject"],
                   request.form["question"],
                   request.form["option1"],
                   request.form["option2"],
                   request.form["option3"],
                   request.form["option4"],
                   request.form["answer"]))

        conn.commit()
        conn.close()

        return redirect("/teacher_dashboard")

    return render_template("add_exam.html")

@app.route("/manage_questions")
def manage_questions():
    if "teacher_name" not in session:
        return redirect("/teacher")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM exams WHERE subject = ?",
              (session["subject"],))
    questions = c.fetchall()
    conn.close()

    return render_template("manage_questions.html",
                           questions=questions,
                           subject=session["subject"])

@app.route("/delete_question/<int:question_id>")
def delete_question(question_id):
    if "teacher_name" not in session:
        return redirect("/teacher")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""DELETE FROM exams
                 WHERE id = ? AND subject = ?""",
              (question_id, session["subject"]))

    conn.commit()
    conn.close()

    return redirect("/manage_questions")

@app.route("/scorecard")
def scorecard():
    if "teacher_name" not in session:
        return redirect("/teacher")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""SELECT id, student_name, roll_no, teacher_name, subject, score, warnings,
                        COALESCE(mobile_warnings, 0), COALESCE(eye_warnings, 0)
                 FROM results WHERE subject = ?""",
              (session["subject"],))
    data = c.fetchall()

    conn.close()

    return render_template("scorecard.html",
                           results=data,
                           subject=session["subject"],
                           teacher=session["teacher_name"])

@app.route("/delete_result/<int:result_id>")
def delete_result(result_id):
    if "teacher_name" not in session:
        return redirect("/teacher")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""DELETE FROM results
                 WHERE id = ? AND subject = ?""",
              (result_id, session["subject"]))

    conn.commit()
    conn.close()

    return redirect("/scorecard")

# ================= STUDENT LOGIN =================

@app.route("/student", methods=["GET", "POST"])
def student():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT DISTINCT subject FROM exams")
    subjects = c.fetchall()

    if request.method == "POST":
        name = request.form["student_name"]
        roll_no = request.form["roll_no"]
        password = request.form["password"]
        subject = request.form["subject"]

        c.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,))
        student = c.fetchone()

        if student:
            if not check_password_hash(student[3], password):
                conn.close()
                return "Invalid Password"
        else:
            hashed_password = generate_password_hash(password)
            c.execute("INSERT INTO students(name, roll_no, password) VALUES (?,?,?)",
                      (name, roll_no, hashed_password))
            conn.commit()

        session["student_name"] = name
        session["roll_no"] = roll_no
        session["exam_subject"] = subject

        conn.close()
        return redirect("/exam")

    conn.close()
    return render_template("student_login.html", subjects=subjects)

# ================= EXAM =================

@app.route("/exam", methods=["GET", "POST"])
def exam():
    if "exam_subject" not in session:
        return redirect("/student")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM exams WHERE subject = ?",
              (session["exam_subject"],))
    questions = c.fetchall()

    if request.method == "POST":
        score = 0
        warnings = int(request.form.get("warnings") or 0)
        mobile_warnings = int(request.form.get("mobile_warnings") or 0)
        eye_warnings = int(request.form.get("eye_warnings") or 0)

        teacher_name = questions[0][1] if questions else ""
        subject = session["exam_subject"]

        for q in questions:
            selected = request.form.get(str(q[0]))
            if selected == q[8]:
                score += 1

        c.execute("""INSERT INTO results(student_name, roll_no, teacher_name,
                    subject, score, warnings, mobile_warnings, eye_warnings)
                    VALUES (?,?,?,?,?,?,?,?)""",
                (session["student_name"],
                 session["roll_no"],
                 teacher_name,
                 subject,
                 score,
                 warnings,
                 mobile_warnings,
                 eye_warnings))

        conn.commit()
        conn.close()

        return render_template("result.html",
                               score=score,
                               total=len(questions),
                               warnings=warnings,
                               mobile_warnings=mobile_warnings,
                               eye_warnings=eye_warnings)

    conn.close()
    return render_template("exam.html",
                           questions=questions,
                           subject=session["exam_subject"])

if __name__ == "__main__":
    app.run(debug=True)