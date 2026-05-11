from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
import os, sqlite3, csv, re, json
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from utils.database_setup import init_db, save_feedback
from model.classes import User, RecommendationEngine, TravelPlan, Admin
from model.chatbot_logic import get_chat_response
from model.recommender import get_recommendations, get_more_recommendations, get_detailed_itinerary
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
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

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
try:
    init_db()
except sqlite3.Error as e:
    print("⚠ Database initialization skipped:", e)

# ---------------- FAVICON ----------------
@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(app.static_folder, 'images', 'favicon.ico'), mimetype='image/x-icon') if os.path.exists(os.path.join(app.static_folder, 'images', 'favicon.ico')) else ('', 204)

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
    email = request.form.get('number') # Using number field as email for now

    if not username or not password:
        flash("⚠ Username and Password are required!", "error")
        return redirect(url_for('user_auth'))

    if User.create(username, password, email):
        flash("✅ Account created successfully! Please sign in.", "success")
    else:
        flash("⚠ Username already exists or error occurred!", "error")

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
    user = User.login(username, password)
    if user:
        session['user_logged_in'] = True
        session['username'] = user.name
        session['user_id'] = user.userid
        flash(f"👋 Welcome back, {user.name}!", "success")
        return redirect(url_for('user_dashboard'))
    else:
        flash("❌ Invalid username or password!", "error")
        return redirect(url_for('user_auth'))


# ---------------- GOOGLE OAUTH ----------------
@app.route('/auth/google')
def google_login():
    if not os.getenv('GOOGLE_CLIENT_ID') or not os.getenv('GOOGLE_CLIENT_SECRET'):
        flash("⚠ Google Sign-In is not configured. Please use username/password login.", "error")
        return redirect(url_for('user_auth'))
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

@app.route('/dashboard')
def dashboard_redirect():
    return redirect(url_for('user_dashboard'))

@app.route('/auth')
def auth_redirect():
    return redirect(url_for('user_auth'))


# ---------------- ADMIN LOGIN ----------------
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
        from utils.database_setup import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()

        users = Admin.manageUsers()

        # ✅ Fetch feedbacks
        cur.execute("SELECT name, email, message, created_at FROM feedback ORDER BY created_at DESC")
        feedbacks = cur.fetchall()

        user_count = len(users)
        
        destinations = Admin.manageDestinations()

        conn.close()
    except Exception as e:
        print("⚠ Database error:", e)
        users, feedbacks, user_count, destinations = [], [], 0, []

    return render_template(
        'admin.html',
        users=users,
        feedbacks=feedbacks,
        user_count=user_count,
        destinations=destinations,
        admin_name=session.get('admin_name', 'Admin')
    )


# ---------------- CHATBOT ----------------
@app.route('/ai_chat', methods=['POST'])
def ai_chat():
    user_msg = request.json.get('msg', '')
    reply = chat_with_gemini(user_msg)

    return jsonify({'reply': reply})


# ---------------- TRAVEL RECOMMENDER (5 Places) ----------------
@app.route('/recommend', methods=['POST'])
def recommend():
    location = request.form.get('location')
    interest = request.form.get('interest')
    budget = request.form.get('budget', '5000')
    travel_mode = request.form.get('travel_mode', 'car')
    place_types = request.form.get('place_types', '')
    season = request.form.get('season', '')
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    
    try:
        if start_date and end_date:
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            duration_int = max(1, (d2 - d1).days + 1)
        else:
            duration_int = int(request.form.get('duration', '3'))
    except ValueError:
        duration_int = 3

    try:
        budget_float = float(budget)
    except ValueError:
        budget_float = 5000

    # Update user preferences if logged in
    if session.get('user_logged_in') and session.get('user_id'):
        try:
            user = User(userid=session.get('user_id'), name=session.get('username'))
            user.enterPreferences(budget_float, duration_int, place_types, season)
        except sqlite3.Error as e:
            print("⚠ Could not save user preferences:", e)

    # Get 5 destination suggestions from AI
    ai_results = RecommendationEngine.suggestDestinations(
        location, interest, budget, travel_mode, duration_int, place_types, season, start_date, end_date
    )

    try:
        weather = get_weather(location)
    except Exception:
        weather = None

    # Store search params in session for "Show More" feature
    session['last_search'] = {
        'location': location,
        'interest': interest,
        'budget': budget,
        'travel_mode': travel_mode,
        'duration': duration_int,
        'place_types': place_types,
        'season': season,
        'start_date': start_date,
        'end_date': end_date
    }

    return render_template(
        'result.html',
        location=location,
        interest=interest,
        budget=budget,
        travel_mode=travel_mode,
        duration=duration_int,
        place_types=place_types,
        season=season,
        start_date=start_date,
        end_date=end_date,
        results=ai_results,
        weather=weather
    )


# ---------------- SHOW MORE PLACES (AJAX) ----------------
@app.route('/recommend/more', methods=['POST'])
def recommend_more():
    data = request.json
    exclude_places = data.get('exclude', [])
    
    search = session.get('last_search', {})
    if not search:
        return jsonify({"error": "No previous search found."}), 400

    results = get_more_recommendations(
        search.get('location', ''),
        search.get('interest', ''),
        search.get('budget', '5000'),
        search.get('travel_mode', 'car'),
        search.get('duration', 3),
        search.get('place_types', ''),
        search.get('season', ''),
        exclude_places,
        search.get('start_date', ''),
        search.get('end_date', '')
    )
    return jsonify(results)


# ---------------- DETAILED ITINERARY (Selected Place) ----------------
@app.route('/itinerary', methods=['POST'])
def itinerary():
    destination = request.form.get('destination', '')
    location = request.form.get('location', '')
    interest = request.form.get('interest', '')
    budget = request.form.get('budget', '5000')
    travel_mode = request.form.get('travel_mode', 'car')
    duration = request.form.get('duration', '3')
    season = request.form.get('season', '')
    place_types = request.form.get('place_types', '')
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')

    try:
        duration_int = int(duration)
    except ValueError:
        duration_int = 3

    # Get detailed day-wise itinerary from AI
    itinerary_data = get_detailed_itinerary(
        location, destination, interest, budget, travel_mode, duration_int, season, start_date, end_date
    )

    return render_template(
        'itinerary.html',
        destination=destination,
        location=location,
        interest=interest,
        budget=budget,
        travel_mode=travel_mode,
        duration=duration_int,
        season=season,
        place_types=place_types,
        start_date=start_date,
        end_date=end_date,
        itinerary=itinerary_data
    )


# ---------------- SAVE TRIP ----------------
@app.route('/save-trip', methods=['POST'])
def save_trip():
    if not session.get('user_logged_in'):
        return jsonify({"success": False, "message": "Please log in to save trips."}), 401

    data = request.json
    username = session.get('username')
    user_id = session.get('user_id')
    destination = data.get('destination', data.get('location', ''))
    duration = data.get('duration', 3)
    budget = data.get('budget', '5000')
    interest = data.get('interest', '')
    place_types = data.get('place_types', '')
    season = data.get('season', '')
    travel_mode = data.get('travel_mode', '')
    itinerary_json = data.get('itinerary_json', '')
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    
    try:
        total_cost = float(budget)
    except (ValueError, TypeError):
        total_cost = 5000

    try:
        plan_id = TravelPlan.createPlan(
            user_id=user_id,
            destination_name=destination,
            duration=duration,
            total_cost=total_cost,
            interest=interest,
            place_types=place_types,
            season=season,
            travel_mode=travel_mode,
            itinerary_json=itinerary_json,
            start_date=start_date,
            end_date=end_date
        )
        return jsonify({"success": True, "message": f"Trip saved successfully! (Plan ID: {plan_id})"})
    except Exception as e:
        print("Error saving trip:", e)
        return jsonify({"success": False, "message": "Failed to save trip."}), 500


# ---------------- TRIP HISTORY ----------------
@app.route('/history')
def trip_history():
    if not session.get('user_logged_in'):
        flash("⚠ Please sign in first!", "error")
        return redirect(url_for('user_auth'))
    
    user_id = session.get('user_id')
    history = TravelPlan.getUserHistory(user_id)
    return render_template('history.html', history=history, username=session.get('username'))


@app.route('/api/history')
def api_history():
    if not session.get('user_logged_in'):
        return jsonify({"error": "Not logged in"}), 401
    
    user_id = session.get('user_id')
    history = TravelPlan.getUserHistory(user_id)
    return jsonify({"history": history})


@app.route('/api/history/delete', methods=['POST'])
def delete_history():
    if not session.get('user_logged_in'):
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.json
    plan_id = data.get('plan_id')
    user_id = session.get('user_id')
    
    try:
        TravelPlan.deletePlan(plan_id, user_id)
        return jsonify({"success": True, "message": "Trip deleted."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


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
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )
