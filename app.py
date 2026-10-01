from flask import Flask, render_template, request, redirect, session
import os
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secretkey"

# ================= DATABASE CONFIGURATION =================
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "root123")
DB_NAME = os.environ.get("DB_NAME", "exam_proctoring")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        autocommit=True
    )

def init_db():
    # Ensure MySQL database exists
    try:
        server_conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            autocommit=True
        )
        with server_conn.cursor() as s_cursor:
            s_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        server_conn.close()
    except Exception as e:
        print(f"Database check warning: {e}")

    conn = get_db()
    with conn.cursor() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS teachers(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) UNIQUE,
                        subject VARCHAR(100),
                        department VARCHAR(100) DEFAULT '',
                        password VARCHAR(255)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')

        c.execute('''CREATE TABLE IF NOT EXISTS students(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100),
                        roll_no VARCHAR(50) UNIQUE,
                        department VARCHAR(100) DEFAULT '',
                        class VARCHAR(50) DEFAULT '',
                        password VARCHAR(255)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')

        c.execute('''CREATE TABLE IF NOT EXISTS exams(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        teacher_name VARCHAR(100),
                        subject VARCHAR(100),
                        question TEXT,
                        option1 TEXT,
                        option2 TEXT,
                        option3 TEXT,
                        option4 TEXT,
                        answer TEXT
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')

        c.execute('''CREATE TABLE IF NOT EXISTS results(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        student_name VARCHAR(100),
                        roll_no VARCHAR(50),
                        teacher_name VARCHAR(100),
                        subject VARCHAR(100),
                        department VARCHAR(100) DEFAULT '',
                        score INT DEFAULT 0,
                        warnings INT DEFAULT 0,
                        mobile_warnings INT DEFAULT 0,
                        eye_warnings INT DEFAULT 0,
                        tab_warnings INT DEFAULT 0,
                        face_warnings INT DEFAULT 0
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')

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

        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT id, name, subject, department, password FROM teachers WHERE name = %s", (name,))
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

        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT id FROM teachers WHERE name = %s", (name,))
        if c.fetchone():
            conn.close()
            return render_template("teacher_register.html", error="Teacher name already registered! Please login.")

        hashed_password = generate_password_hash(password)
        c.execute("""INSERT INTO teachers(name, subject, department, password)
                     VALUES (%s, %s, %s, %s)""",
                  (name, subject, department, hashed_password))
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
        conn = get_db()
        c = conn.cursor()

        c.execute("""INSERT INTO exams(teacher_name, subject, question,
                    option1, option2, option3, option4, answer)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                  (session["teacher_name"],
                   session["subject"],
                   request.form["question"],
                   request.form["option1"],
                   request.form["option2"],
                   request.form["option3"],
                   request.form["option4"],
                   request.form["answer"]))

        conn.close()

        return redirect("/teacher_dashboard")

    return render_template("add_exam.html")

@app.route("/manage_questions")
def manage_questions():
    if "teacher_name" not in session:
        return redirect("/teacher")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM exams WHERE subject = %s",
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

    conn = get_db()
    c = conn.cursor()

    c.execute("""DELETE FROM exams
                 WHERE id = %s AND subject = %s""",
              (question_id, session["subject"]))

    conn.close()

    return redirect("/manage_questions")

@app.route("/scorecard")
def scorecard():
    if "teacher_name" not in session:
        return redirect("/teacher")

    conn = get_db()
    c = conn.cursor()

    c.execute("""SELECT r.id,
                        r.roll_no,
                        r.student_name,
                        COALESCE(NULLIF(r.department, ''), NULLIF(s.department, ''), 'General') AS department,
                        r.subject,
                        r.warnings,
                        r.score
                 FROM results r
                 LEFT JOIN students s ON r.roll_no = s.roll_no
                 WHERE r.subject = %s
                 ORDER BY r.id DESC""",
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

    conn = get_db()
    c = conn.cursor()

    c.execute("""DELETE FROM results
                 WHERE id = %s AND subject = %s""",
              (result_id, session["subject"]))

    conn.close()

    return redirect("/scorecard")

# ================= STUDENT AUTH =================

@app.route("/student", methods=["GET", "POST"])
def student():
    conn = get_db()
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

        c.execute("SELECT id, name, roll_no, department, class, password FROM students WHERE roll_no = %s", (roll_no,))
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

        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT id FROM students WHERE roll_no = %s", (roll_no,))
        if c.fetchone():
            conn.close()
            return render_template("student_register.html", error="Roll number already registered! Please login.")

        hashed_password = generate_password_hash(password)
        c.execute("""INSERT INTO students(name, roll_no, department, class, password)
                     VALUES (%s, %s, %s, %s, %s)""",
                  (name, roll_no, department, student_class, hashed_password))
        conn.close()

        return redirect("/student?registered=1")

    return render_template("student_register.html")

# ================= EXAM =================

@app.route("/exam", methods=["GET", "POST"])
def exam():
    if "exam_subject" not in session:
        return redirect("/student")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM exams WHERE subject = %s",
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

        department = session.get("department", "")

        c.execute("""INSERT INTO results(student_name, roll_no, teacher_name,
                    subject, department, score, warnings, mobile_warnings, eye_warnings,
                    tab_warnings, face_warnings)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (session["student_name"],
                 session["roll_no"],
                 teacher_name,
                 subject,
                 department,
                 score,
                 warnings,
                 mobile_warnings,
                 eye_warnings,
                 tab_warnings,
                 face_warnings))

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