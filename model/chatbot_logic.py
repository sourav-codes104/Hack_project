def get_chat_response(user_input):
    user_input = user_input.lower()
    if "hello" in user_input or "hi" in user_input:
        return "Hey traveler! 👋 Ready for your next adventure?"
    elif "place" in user_input:
        return "You can visit Rajwada Palace or Choral Dam near Indore!"
    elif "weather" in user_input:
        return "It's a sunny day ☀️, perfect for exploration!"
    elif "thank" in user_input:
        return "You're welcome! 😊"
    else:
        return "I'm still learning! Try asking about places, weather, or greetings."
