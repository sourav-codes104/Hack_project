from flask import Flask, render_template, request, jsonify
from model.chatbot_logic import get_chat_response
from model.recommender import get_recommendations
from utils.weather_app import get_weather

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    location = request.form.get('location')
    interest = request.form.get('interest')
    budget = request.form.get('budget')

    results = get_recommendations(location, interest, budget)
    weather = get_weather(location)
    return render_template('result.html', results=results, location=location, weather=weather)

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.form['msg']
    reply = get_chat_response(user_msg)
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
