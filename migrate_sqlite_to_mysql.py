import sqlite3
import pymysql

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root123"
DB_NAME = "exam_proctoring"
SQLITE_FILE = "database.db"

def migrate():
    print("Connecting to MySQL...")
    # Step 1: Connect to MySQL server (without DB) to create database
    server_conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, autocommit=True)
    server_cursor = server_conn.cursor()
    server_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    server_conn.close()
    print(f"Database `{DB_NAME}` ready.")

    # Step 2: Connect to exam_proctoring in MySQL
    my_conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, autocommit=True)
    my_cursor = my_conn.cursor()

    # Step 3: Create Tables in MySQL
    my_cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) UNIQUE,
        subject VARCHAR(100),
        department VARCHAR(100) DEFAULT '',
        password VARCHAR(255)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    my_cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        roll_no VARCHAR(50) UNIQUE,
        department VARCHAR(100) DEFAULT '',
        class VARCHAR(50) DEFAULT '',
        password VARCHAR(255)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    my_cursor.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id INT AUTO_INCREMENT PRIMARY KEY,
        teacher_name VARCHAR(100),
        subject VARCHAR(100),
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        answer TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    my_cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    print("Tables created in MySQL.")

    # Step 4: Migrate data from SQLite
    sq_conn = sqlite3.connect(SQLITE_FILE)
    sq_cursor = sq_conn.cursor()

    # 1. Teachers
    sq_cursor.execute("SELECT id, name, subject, COALESCE(department, ''), password FROM teachers")
    teachers = sq_cursor.fetchall()
    for t in teachers:
        my_cursor.execute("""
            INSERT INTO teachers (id, name, subject, department, password)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE name=VALUES(name), subject=VALUES(subject), department=VALUES(department), password=VALUES(password)
        """, t)
    print(f"Migrated {len(teachers)} teachers.")

    # 2. Students
    sq_cursor.execute("SELECT id, name, roll_no, COALESCE(department, ''), COALESCE(class, ''), password FROM students")
    students = sq_cursor.fetchall()
    for s in students:
        my_cursor.execute("""
            INSERT INTO students (id, name, roll_no, department, class, password)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE name=VALUES(name), department=VALUES(department), class=VALUES(class), password=VALUES(password)
        """, s)
    print(f"Migrated {len(students)} students.")

    # 3. Exams
    sq_cursor.execute("SELECT id, teacher_name, subject, question, option1, option2, option3, option4, answer FROM exams")
    exams = sq_cursor.fetchall()
    for e in exams:
        my_cursor.execute("""
            INSERT INTO exams (id, teacher_name, subject, question, option1, option2, option3, option4, answer)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE question=VALUES(question), answer=VALUES(answer)
        """, e)
    print(f"Migrated {len(exams)} exam questions.")

    # 4. Results
    sq_cursor.execute("""SELECT id, student_name, roll_no, teacher_name, subject,
                                COALESCE(department, ''), score, warnings,
                                COALESCE(mobile_warnings, 0), COALESCE(eye_warnings, 0),
                                COALESCE(tab_warnings, 0), COALESCE(face_warnings, 0)
                         FROM results""")
    results = sq_cursor.fetchall()
    for r in results:
        my_cursor.execute("""
            INSERT INTO results (id, student_name, roll_no, teacher_name, subject,
                                department, score, warnings, mobile_warnings, eye_warnings,
                                tab_warnings, face_warnings)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE score=VALUES(score), warnings=VALUES(warnings)
        """, r)
    print(f"Migrated {len(results)} results.")

    sq_conn.close()
    my_conn.close()
    print("Migration from SQLite to MySQL completed successfully!")

if __name__ == "__main__":
    migrate()
