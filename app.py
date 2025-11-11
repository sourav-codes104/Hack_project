from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
import os, sqlite3, csv, re
from dotenv import load_dotenv
import google.generativeai as genai
from utils.database_setup import init_db, save_feedback, create_user, validate_user
from model.chatbot_logic import get_chat_response
from model.recommender import get_recommendations
from utils.weather_app import get_weather
from model.conversational_ai import chat_with_gemini
from authlib.integrations.flask_client import OAuth

# ✅ DB path constant
DB_PATH = os.path.join(os.getcwd(), "database", "travel.db")

# ✅ Flask setup
app = Flask(
    __name__,
    template_folder=os.path.join(os.getcwd(), 'templates'),
    static_folder=os.path.join(os.getcwd(), 'static')
)
app.secret_key = "super_secret_key_2025"

# ✅ Load environment variables
load_dotenv()

# ✅ Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Google OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'}
)

# ✅ Initialize database
init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- USER AUTH ----------------
@app.route('/user_auth')
def user_auth():
    session.pop('username', None)
    session.pop('user_logged_in', None)
    return render_template('user_auth.html')


@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')
    number = request.form.get('number')

    if not username or not password or not number:
        flash("⚠ All fields are required!", "error")
        return redirect(url_for('user_auth'))

    if create_user(username, password, number):
        flash("✅ Account created successfully! Please sign in.", "success")
    else:
        flash("⚠ Username already exists!", "error")

    return redirect(url_for('user_auth'))


@app.route('/signin', methods=['POST'])
def signin():
    username = request.form.get('username')
    password = request.form.get('password')

    # Admin login
    if username == 'Sourav' and password == '12345':
        session['admin_logged_in'] = True
        session['admin_name'] = 'Sourav'
        flash("✅ Admin login successful!", "success")
        return redirect(url_for('admin_dashboard'))

    # Normal user login
    if validate_user(username, password):
        session['user_logged_in'] = True
        session['username'] = username
        flash(f"👋 Welcome back, {username}!", "success")
        return redirect(url_for('user_dashboard'))
    else:
        flash("❌ Invalid username or password!", "error")
        return redirect(url_for('user_auth'))


# ---------------- GOOGLE OAUTH ----------------
@app.route('/auth/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    session['user_logged_in'] = True
    session['username'] = user_info['name']
    session['email'] = user_info['email']
    session['profile_pic'] = user_info['picture']
    flash(f"👋 Welcome, {user_info['name']}!", "success")
    return redirect(url_for('user_dashboard'))


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("👋 Logged out successfully!", "info")
    return redirect(url_for('user_auth'))


# ---------------- USER DASHBOARD ----------------
@app.route('/user')
def user_dashboard():
    if not session.get('user_logged_in'):
        flash("⚠ Please sign in first!", "error")
        return redirect(url_for('user_auth'))
    return render_template('user.html', username=session.get('username'))


# ---------------- ADMIN LOGIN ----------------
@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'Sourav' and password == '12345':
            session['admin_logged_in'] = True
            session['admin_name'] = 'Sourav'
            flash("✅ Login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("❌ Invalid username or password!", "error")
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')



# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash("🚫 Please log in first!", "error")
        return redirect(url_for('admin_login'))

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # ✅ Fetch users
        cur.execute("SELECT username, number, created_at FROM users ORDER BY created_at DESC")
        users = cur.fetchall()

        # ✅ Fetch feedbacks
        cur.execute("SELECT name, email, message, created_at FROM feedback ORDER BY created_at DESC")
        feedbacks = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]

        conn.close()
    except Exception as e:
        print("⚠ Database error:", e)
        users, feedbacks, user_count = [], [], 0

    return render_template(
        'admin.html',
        users=users,
        feedbacks=feedbacks,
        user_count=user_count,
        admin_name=session.get('admin_name', 'Admin')
    )


# ---------------- CHATBOT ----------------
@app.route('/ai_chat', methods=['POST'])
def ai_chat():
    user_msg = request.json.get('msg', '')
    reply = chat_with_gemini(user_msg)

    def clean_reply(s):
        s = re.sub(r'<[^>]+>', '', s)
        s = re.sub(r'[*#`_~\-•→]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    text = clean_reply(reply)
    words = text.split()
    if len(words) > 25:
        text = ' '.join(words[:25]) + '...'

    return jsonify({'reply': text})


# ---------------- TRAVEL RECOMMENDER ----------------
@app.route('/recommend', methods=['POST'])
def recommend():
    location = request.form.get('location')
    interest = request.form.get('interest')
    budget = request.form.get('budget')
    travel_mode = request.form.get('travel_mode', 'car')

    ai_results = get_recommendations(location, interest, budget, travel_mode)

    try:
        weather = get_weather(location)
    except Exception:
        weather = None

    return render_template(
        'result.html',
        location=location,
        interest=interest,
        budget=budget,
        travel_mode=travel_mode,
        results=ai_results,
        weather=weather
    )


# ---------------- DATABASE MANAGEMENT ----------------
@app.route("/admin/manage_db/<action>")
def manage_db(action):
    """Admin tools: remove duplicates, export, etc."""
    if not session.get('admin_logged_in'):
        return jsonify({"message": "❌ Unauthorized access!"}), 403

    message = ""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        if action == "clean_duplicates":
            cur.execute("""
                DELETE FROM users
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM users
                    GROUP BY username
                );
            """)
            deleted = cur.rowcount
            conn.commit()
            message = f"✅ {deleted} duplicate user(s) deleted."

        elif action == "check_integrity":
            cur.execute("PRAGMA integrity_check;")
            result = cur.fetchone()[0]
            message = "✅ Database integrity is OK." if result == "ok" else f"⚠ Issue: {result}"

        elif action == "export_data":
            export_path = os.path.join(os.getcwd(), "database", "users_export.csv")
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            with open(export_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Username", "Mobile", "Created_At"])
                cur.execute("SELECT username, number, created_at FROM users")
                writer.writerows(cur.fetchall())
            conn.close()
            return send_file(export_path, as_attachment=True, download_name="users_export.csv")

        else:
            message = "❌ Unknown action."

    except Exception as e:
        message = f"⚠ Error: {str(e)}"

    finally:
        try:
            conn.close()
        except:
            pass

    return jsonify({"message": message})


# ---------------- FEEDBACK EXPORT ----------------
@app.route('/admin/export_feedback')
def export_feedback():
    if not session.get('admin_logged_in'):
        flash("❌ Unauthorized access!", "error")
        return redirect(url_for('admin_login'))

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        export_path = os.path.join(os.getcwd(), "database", "feedback_export.csv")

        with open(export_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Email", "Message", "Created_At"])
            cur.execute("SELECT name, email, message, created_at FROM feedback")
            writer.writerows(cur.fetchall())

        conn.close()
        return send_file(export_path, as_attachment=True, download_name="feedback_export.csv")
    except Exception as e:
        flash(f"⚠ Error exporting feedback: {str(e)}", "error")
        return redirect(url_for('admin_dashboard'))


# ---------------- FEEDBACK FORM ----------------
@app.route('/feedback', methods=['POST'])
def feedback():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    save_feedback(name, email, message)
    flash("✅ Feedback submitted successfully!", "success")
    return redirect(url_for('home'))


# ---------------- TEST ROUTE ----------------
@app.route('/test')
def test():
    return "<h2>✅ Flask Connected — All Routes Working!</h2>"


# ---------------- MAIN ----------------
if __name__ == '__main__':
    print("✅ AI TravelMate running with Gemini AI + OAuth + Admin Tools + TTS")
    app.run(debug=True)
