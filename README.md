# 🎓 AI-Powered Online Exam Proctoring System

An intelligent, production-grade online examination proctoring web application built with **Flask**, **MySQL**, and client-side computer vision (**MediaPipe** & **TensorFlow.js**). The platform monitors student behavior in real time during exams to detect cheating, tab switches, and unauthorized devices while providing a clean dashboard for teachers and students.

---

## 🌟 Key Features

### 👁️ Real-Time Client-Side AI Proctoring
- **Iris & Gaze Deviation Tracking**: Uses MediaPipe Face Mesh to monitor eye gaze and head rotation in real-time, detecting when the student looks away from the screen.
- **Mobile Phone Detection**: Employs TensorFlow.js COCO-SSD model running directly in the browser to detect cell phones/smartphones.
- **Multiple People Detection**: Flags when more than one face or body appears in the camera frame.
- **Tab Switching & Window Blur Detection**: Listens to browser visibility state to detect students switching tabs or minimizing the browser window.
- **Automated Warning System**: Accumulates violations and displays real-time warning alerts.

### 👨‍🎓 Student Portal
- **Secure Registration**: Register with Name, Department, Class, Roll Number, and Password (hashed with Werkzeug).
- **Exam Portal**: Select available exam subject, read questions, take the exam with active video feed & proctoring indicators.
- **Detailed Result Summary**: Displays score along with a categorized breakdown of warnings (mobile, gaze, tab switch, multiple people).

### 👩‍🏫 Teacher Portal
- **Authentication**: Dedicated teacher registration and login.
- **Exam Management**: Add questions with 4 multiple-choice options and designated correct answer.
- **Question Bank**: View and delete questions by subject.
- **Scorecard Dashboard**: Clean overview displaying:
  - Roll Number
  - Student Name
  - Department
  - Subject
  - Total Warnings
  - Proctoring Status (✅ Normal vs ⚠️ Flagged)
  - Score
  - Action (Delete result record)

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Flask 3.x, Werkzeug (Password hashing)
- **Database**: MySQL 8.0 / MySQL Workbench, PyMySQL
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla ES6+)
- **AI / Computer Vision**:
  - [MediaPipe Face Mesh](https://github.com/google/mediapipe) (Iris & Face tracking)
  - [TensorFlow.js COCO-SSD](https://github.com/tensorflow/tfjs-models/tree/master/coco-ssd) (Object detection for mobile phones & people)
- **WSGI Production Server**: Gunicorn
- **Containerization**: Docker, Docker Compose

---

## 📁 Project Structure

```text
examproctoring/
├── app.py                      # Core Flask Application & API Routes
├── schema.sql                  # MySQL Database Schema
├── requirements.txt            # Python Dependencies
├── Procfile                    # Heroku / Render / Railway Deployment Procfile
├── Dockerfile                  # Containerized Build Specification
├── docker-compose.yml          # Full-Stack Compose (Web + MySQL 8.0)
├── .env.example                # Template for Environment Configuration
├── .gitignore                  # Git Ignore Rules
├── static/
│   ├── proctor.js              # Real-Time AI Proctoring Engine (TF.js + MediaPipe)
│   ├── style.css               # Global & Navigation Styles
│   ├── teacher.css             # Teacher Portal Styles
│   ├── add_exam.css            # Exam Creation Styles
│   ├── scorecard.css           # Scorecard Table Styles
│   └── result.css              # Result Page Styles
└── templates/
    ├── index.html              # Landing Page
    ├── student_login.html      # Student Authentication
    ├── student_register.html   # Student Registration
    ├── teacher_login.html      # Teacher Authentication
    ├── teacher_register.html   # Teacher Registration
    ├── teacher_dashboard.html  # Teacher Hub
    ├── add_exam.html           # Exam Question Creator
    ├── manage_questions.html   # Question Bank
    ├── exam.html               # Live Proctored Exam Interface
    ├── result.html             # Student Exam Result
    └── scorecard.html          # Teacher Scorecard View
```

---

## 🚀 Quickstart (Local Development)

### 1. Prerequisites
- Python 3.10+
- MySQL Server 8.0+ (or MySQL Workbench)
- Git

### 2. Clone & Setup Environment
```bash
git clone https://github.com/<your-username>/exam-proctoring.git
cd exam-proctoring

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your MySQL credentials:
```ini
SECRET_KEY=your_random_secret_key_here
FLASK_DEBUG=True
PORT=5000

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=exam_proctoring
DB_PORT=3306
DB_SSL=false
```

### 4. Initialize Database
You can initialize the database using MySQL Workbench or CLI:
```bash
mysql -u root -p < schema.sql
```
*(Alternatively, `app.py` will automatically create the tables on its first startup).*

### 5. Run the Application
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your web browser.

---

## 🐳 Running with Docker

You can run the application and MySQL server together with a single command:

```bash
docker compose up --build -d
```
- Web Application: [http://localhost:5000](http://localhost:5000)
- Health Check: [http://localhost:5000/health](http://localhost:5000/health)
- MySQL Database: `localhost:3306`

---

## ☁️ Production Deployment Guide

### Option 1: Render (Recommended Free/Low Cost)
1. Fork or push this repository to your GitHub account.
2. Sign up at [Render.com](https://render.com).
3. **Create Database**:
   - Create a **New MySQL** database (or use a free managed MySQL service such as [Aiven.io](https://aiven.io) or [Railway](https://railway.app)).
   - Copy the database connection URL or credentials.
4. **Create Web Service**:
   - Click **New +** -> **Web Service**.
   - Connect your GitHub repository.
   - Environment: `Python` (or `Docker`).
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. **Environment Variables**:
   Add the following in Render Dashboard -> **Environment**:
   - `SECRET_KEY`: A secure random string
   - `DATABASE_URL`: `mysql://username:password@host:port/exam_proctoring`
   - `DB_SSL`: `true` (if required by your cloud database)
6. Click **Deploy Web Service**.

### Option 2: Railway
1. Go to [Railway.app](https://railway.app) and click **New Project**.
2. Select **Provision MySQL**.
3. In the same project, click **New Service** -> **GitHub Repo** and choose this repository.
4. Add reference variables:
   - `DATABASE_URL`: `${{MySQL.MYSQL_URL}}`
   - `SECRET_KEY`: Generate a random string.
5. Railway will automatically build via `Dockerfile` or `Procfile` and deploy your app with a public HTTPS URL.

### Option 3: VPS (Ubuntu / AWS EC2 / DigitalOcean)
```bash
# 1. Update and install Docker
sudo apt update && sudo apt install -y docker.io docker-compose git

# 2. Clone repo
git clone https://github.com/<your-username>/exam-proctoring.git
cd exam-proctoring

# 3. Configure .env
cp .env.example .env
nano .env

# 4. Start services
sudo docker-compose up -d --build
```
Setup Nginx as a reverse proxy with Certbot SSL for HTTPS (required for webcam permissions in production).

> ⚠️ **Important for Production**: Browsers require **HTTPS (SSL)** to access the camera and webcam. In production, always ensure your domain or cloud service has an active SSL certificate (Render and Railway provide this automatically out of the box).

---

## 🛡️ Health & Monitoring

The application includes a built-in health check endpoint:
- `GET /health`
  - Returns `200 OK` with `{"status": "healthy", "database": "connected"}` if the database connection is live.
  - Returns `500 Internal Server Error` if the database is unreachable.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
