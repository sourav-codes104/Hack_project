from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import sqlite3
from utils.database_setup import init_db, save_feedback
from model.chatbot_logic import get_chat_response
from model.recommender import get_recommendations
from utils.weather_app import get_weather

# -----------------------------------------------------
# 🔹 FLASK APP SETUP
# -----------------------------------------------------
app = Flask(
    __name__,
    template_folder=os.path.join(os.getcwd(), 'templates'),
    static_folder=os.path.join(os.getcwd(), 'static')
)
app.secret_key = "super_secret_key_2025"

# Initialize database
init_db()


# -----------------------------------------------------
# 🔹 HOME PAGE
# -----------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')


# -----------------------------------------------------
# 🔹 USER DASHBOARD
# -----------------------------------------------------
@app.route('/user')
def user_dashboard():
    return render_template('user.html')


# -----------------------------------------------------
# 🔹 ADMIN LOGIN PAGE
# -----------------------------------------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    # Always show login page first (clear any old session)
    session.pop('admin_logged_in', None)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # ✅ Simple credentials check
        if username == 'admin' and password == '12345':
            session['admin_logged_in'] = True
            flash("Login successful ✅", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid username or password ❌", "error")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


# -----------------------------------------------------
# 🔹 ADMIN DASHBOARD (Protected)
# -----------------------------------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash("Please log in first 🚫", "error")
        return redirect(url_for('admin_login'))

    try:
        conn = sqlite3.connect("database/travel.db")
        cur = conn.cursor()
        cur.execute("SELECT name, email, message, created_at FROM feedback ORDER BY created_at DESC")
        feedbacks = cur.fetchall()
        conn.close()
    except Exception as e:
        print("⚠️ Database error:", e)
        feedbacks = []

    return render_template('admin.html', feedbacks=feedbacks)


# -----------------------------------------------------
# 🔹 ADMIN LOGOUT
# -----------------------------------------------------
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Logged out successfully 👋", "info")
    return redirect(url_for('home'))


# -----------------------------------------------------
# 🔹 CHATBOT PAGE
# -----------------------------------------------------
@app.route('/chat')
def chat_page():
    return render_template('chat.html')


# -----------------------------------------------------
# 🔹 CHATBOT API (AJAX)
# -----------------------------------------------------
@app.route('/chat/api', methods=['POST'])
def chat_api():
    user_msg = request.json.get('msg', '')
    reply = get_chat_response(user_msg)
    return jsonify({'reply': reply})


# -----------------------------------------------------
# 🔹 RECOMMENDATION RESULT
# -----------------------------------------------------
@app.route('/recommend', methods=['POST'])
def recommend():
    location = request.form.get('location')
    interest = request.form.get('interest')
    budget = request.form.get('budget')

    results = get_recommendations(location, interest, budget)
    weather = get_weather(location)

    return render_template('result.html',
                           location=location,
                           results=results,
                           weather=weather)


# -----------------------------------------------------
# 🔹 FEEDBACK SAVE
# -----------------------------------------------------
@app.route('/feedback', methods=['POST'])
def feedback():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    save_feedback(name, email, message)
    return redirect(url_for('home'))


# -----------------------------------------------------
# 🔹 TEST ROUTE
# -----------------------------------------------------
@app.route('/test')
def test():
    return "<h2>✅ Flask Connected — All Routes Working!</h2>"


# -----------------------------------------------------
# 🔹 RUN APP
# -----------------------------------------------------
if __name__ == '__main__':
    print("✅ AI TravelMate running on http://127.0.0.1:5000/")
    app.run(debug=True)
