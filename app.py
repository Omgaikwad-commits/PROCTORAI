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
                    department TEXT DEFAULT '',
                    password TEXT
                )''')

    # ✅ UPDATED (added roll_no, department, class)
    c.execute('''CREATE TABLE IF NOT EXISTS students(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    roll_no TEXT UNIQUE,
                    department TEXT DEFAULT '',
                    class TEXT DEFAULT '',
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

    # ✅ UPDATED (added roll_no, mobile_warnings, eye_warnings, tab_warnings, face_warnings)
    c.execute('''CREATE TABLE IF NOT EXISTS results(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT,
                    roll_no TEXT,
                    teacher_name TEXT,
                    subject TEXT,
                    score INTEGER,
                    warnings INTEGER,
                    mobile_warnings INTEGER DEFAULT 0,
                    eye_warnings INTEGER DEFAULT 0,
                    tab_warnings INTEGER DEFAULT 0,
                    face_warnings INTEGER DEFAULT 0
                )''')

    # Safe schema migration for existing databases
    c.execute("PRAGMA table_info(teachers)")
    t_cols = [col[1] for col in c.fetchall()]
    if "department" not in t_cols:
        c.execute("ALTER TABLE teachers ADD COLUMN department TEXT DEFAULT ''")

    c.execute("PRAGMA table_info(students)")
    s_cols = [col[1] for col in c.fetchall()]
    if "department" not in s_cols:
        c.execute("ALTER TABLE students ADD COLUMN department TEXT DEFAULT ''")
    if "class" not in s_cols:
        c.execute("ALTER TABLE students ADD COLUMN class TEXT DEFAULT ''")

    c.execute("PRAGMA table_info(results)")
    columns = [col[1] for col in c.fetchall()]
    if "mobile_warnings" not in columns:
        c.execute("ALTER TABLE results ADD COLUMN mobile_warnings INTEGER DEFAULT 0")
    if "eye_warnings" not in columns:
        c.execute("ALTER TABLE results ADD COLUMN eye_warnings INTEGER DEFAULT 0")
    if "tab_warnings" not in columns:
        c.execute("ALTER TABLE results ADD COLUMN tab_warnings INTEGER DEFAULT 0")
    if "face_warnings" not in columns:
        c.execute("ALTER TABLE results ADD COLUMN face_warnings INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================

@app.route("/")
def index():
    return render_template("index.html")

# ================= TEACHER AUTH =================

@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    if request.method == "POST":
        name = request.form["name"].strip()
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("SELECT id, name, subject, department, password FROM teachers WHERE name = ?", (name,))
        t = c.fetchone()
        conn.close()

        if t and check_password_hash(t[4], password):
            session["teacher_name"] = t[1]
            session["subject"] = t[2]
            session["department"] = t[3]
            return redirect("/teacher_dashboard")
        else:
            return render_template("teacher_login.html", error="Invalid teacher name or password.")

    return render_template("teacher_login.html")

@app.route("/teacher_register", methods=["GET", "POST"])
def teacher_register():
    if request.method == "POST":
        name = request.form["name"].strip()
        subject = request.form["subject"].strip()
        department = request.form["department"].strip()
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("SELECT id FROM teachers WHERE name = ?", (name,))
        if c.fetchone():
            conn.close()
            return render_template("teacher_register.html", error="Teacher name already registered! Please login.")

        hashed_password = generate_password_hash(password)
        c.execute("""INSERT INTO teachers(name, subject, department, password)
                     VALUES (?,?,?,?)""",
                  (name, subject, department, hashed_password))
        conn.commit()
        conn.close()

        session["teacher_name"] = name
        session["subject"] = subject
        session["department"] = department
        return redirect("/teacher_dashboard")

    return render_template("teacher_register.html")

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
                        COALESCE(mobile_warnings, 0), COALESCE(eye_warnings, 0),
                        COALESCE(tab_warnings, 0), COALESCE(face_warnings, 0)
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

# ================= STUDENT AUTH =================

@app.route("/student", methods=["GET", "POST"])
def student():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT DISTINCT subject FROM exams")
    subjects = c.fetchall()

    registered = request.args.get("registered")
    success_msg = "Registration successful! Please login to take your exam." if registered else None

    if request.method == "POST":
        roll_no = request.form["roll_no"].strip()
        password = request.form["password"]
        subject = request.form.get("subject", "").strip()

        if not subject:
            conn.close()
            return render_template("student_login.html", subjects=subjects, error="Please select an exam subject.")

        c.execute("SELECT id, name, roll_no, department, class, password FROM students WHERE roll_no = ?", (roll_no,))
        student_row = c.fetchone()

        if not student_row:
            conn.close()
            return render_template("student_login.html", subjects=subjects, error="Roll number not registered! Please register first.")

        if not check_password_hash(student_row[5], password):
            conn.close()
            return render_template("student_login.html", subjects=subjects, error="Invalid password! Please try again.")

        session["student_name"] = student_row[1]
        session["roll_no"] = student_row[2]
        session["department"] = student_row[3]
        session["class"] = student_row[4]
        session["exam_subject"] = subject

        conn.close()
        return redirect("/exam")

    conn.close()
    return render_template("student_login.html", subjects=subjects, success=success_msg)

@app.route("/student_register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        name = request.form["name"].strip()
        department = request.form["department"].strip()
        student_class = request.form["class"].strip()
        roll_no = request.form["roll_no"].strip()
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("SELECT id FROM students WHERE roll_no = ?", (roll_no,))
        if c.fetchone():
            conn.close()
            return render_template("student_register.html", error="Roll number already registered! Please login.")

        hashed_password = generate_password_hash(password)
        c.execute("""INSERT INTO students(name, roll_no, department, class, password)
                     VALUES (?,?,?,?,?)""",
                  (name, roll_no, department, student_class, hashed_password))
        conn.commit()
        conn.close()

        return redirect("/student?registered=1")

    return render_template("student_register.html")

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
        tab_warnings = int(request.form.get("tab_warnings") or 0)
        face_warnings = int(request.form.get("face_warnings") or 0)

        teacher_name = questions[0][1] if questions else ""
        subject = session["exam_subject"]

        for q in questions:
            selected = request.form.get(str(q[0]))
            if selected == q[8]:
                score += 1

        c.execute("""INSERT INTO results(student_name, roll_no, teacher_name,
                    subject, score, warnings, mobile_warnings, eye_warnings,
                    tab_warnings, face_warnings)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (session["student_name"],
                 session["roll_no"],
                 teacher_name,
                 subject,
                 score,
                 warnings,
                 mobile_warnings,
                 eye_warnings,
                 tab_warnings,
                 face_warnings))

        conn.commit()
        conn.close()

        return render_template("result.html",
                               score=score,
                               total=len(questions),
                               warnings=warnings,
                               mobile_warnings=mobile_warnings,
                               eye_warnings=eye_warnings,
                               tab_warnings=tab_warnings,
                               face_warnings=face_warnings)

    conn.close()
    return render_template("exam.html",
                           questions=questions,
                           subject=session["exam_subject"])

if __name__ == "__main__":
    app.run(debug=True)