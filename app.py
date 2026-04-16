from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from datetime import datetime
import cloudinary
import cloudinary.uploader
import os

app = Flask(__name__)
app.secret_key = "secret123"

# =========================
# ☁️ CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name="Root",
    api_key="636221386366614",
    api_secret="_w4z6YMGDQvopHfU4BeAIiEbMaEYOUR_SECRET"
)

# =========================
# ☁️ MONGODB CONNECTION (SAFE)
# =========================
try:
    client = MongoClient(
        "mongodb+srv://iitjeechemistry9_db_user:<db_password>@cluster0.oz4izgc.mongodb.net/?appName=Cluster0", serverSelectionTimeoutMS=5000",
        serverSelectionTimeoutMS=5000,
        tls=True,
        tlsAllowInvalidCertificates=True
    )
    db = client["hrms"]

    users = db["users"]
    attendance = db["attendance"]
    performance = db["performance"]
    files = db["files"]

    print("MongoDB Connected ✅")

except Exception as e:
    print("MongoDB Error ❌:", e)

    # fallback empty (prevents crash)
    users = None
    attendance = None
    performance = None
    files = None


# =========================
# CREATE DEFAULT ADMIN (SAFE)
# =========================
try:
    if users and users.count_documents({"email": "admin@gmail.com"}) == 0:
        users.insert_one({
            "name": "Admin",
            "email": "admin@gmail.com",
            "password": "1234",
            "role": "admin"
        })
except:
    pass


# =========================
# ROUTES
# =========================

# HOME
@app.route('/')
def home():
    return render_template('login.html')


# =========================
# SIGNUP
# =========================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST' and users:
        users.insert_one({
            "name": request.form['name'],
            "email": request.form['email'],
            "password": request.form['password'],
            "role": request.form['role']
        })
        return redirect('/')

    return render_template('signup.html')


# =========================
# LOGIN
# =========================
@app.route('/login', methods=['POST'])
def login():
    if not users:
        return "Database not connected"

    email = request.form['email']
    password = request.form['password']

    user = users.find_one({"email": email, "password": password})

    if user:
        session['email'] = email
        session['role'] = user['role']
        return redirect('/dashboard')
    else:
        return "Invalid Login"


# =========================
# DASHBOARD
# =========================
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect('/')

    return render_template(
        'dashboard.html',
        email=session['email'],
        role=session['role']
    )


# =========================
# ATTENDANCE
# =========================
@app.route('/mark_attendance')
def mark_attendance():
    if 'email' not in session:
        return redirect('/')

    if attendance:
        attendance.insert_one({
            "email": session['email'],
            "date": datetime.now()
        })

    return "Attendance Marked"


# =========================
# VIEW ATTENDANCE
# =========================
@app.route('/view_attendance')
def view_attendance():
    if not attendance:
        return "DB not connected"

    data = attendance.find({"email": session['email']})
    return render_template('attendance.html', records=data)


# =========================
# PERFORMANCE
# =========================
@app.route('/add_performance', methods=['GET', 'POST'])
def add_performance():
    if request.method == 'POST' and performance:
        performance.insert_one({
            "employee": request.form['employee'],
            "rating": request.form['rating'],
            "feedback": request.form['feedback']
        })
        return redirect('/dashboard')

    return render_template('performance.html')


# =========================
# VIEW PERFORMANCE
# =========================
@app.route('/view_performance')
def view_performance():
    if not performance:
        return "DB not connected"

    data = performance.find()
    return render_template('view_performance.html', data=data)


# =========================
# FILE UPLOAD (CLOUDINARY)
# =========================
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'email' not in session:
        return redirect('/')

    if request.method == 'POST':
        file = request.files['file']

        if file:
            result = cloudinary.uploader.upload(file)

            file_url = result['secure_url']

            if files:
                files.insert_one({
                    "email": session['email'],
                    "file_url": file_url,
                    "date": datetime.now()
                })

            return "File Uploaded Successfully"

    return render_template('upload.html')


# =========================
# VIEW FILES
# =========================
@app.route('/my_files')
def my_files():
    if 'email' not in session:
        return redirect('/')

    if not files:
        return "DB not connected"

    user_files = files.find({"email": session['email']})
    return render_template('files.html', files=user_files)


# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# =========================
# PORT FIX (IMPORTANT)
# =========================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5500))
    app.run(host="0.0.0.0", port=port)