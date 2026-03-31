# chatbot_mock.py
import random

print("Welcome to Terminal Chatbot! Type 'exit' to quit.\n")

# A simple list of simulated responses
responses = {
    "hello": ["Hi there!", "Hello! How are you?", "Hey! Good to see you."],
    "how are you": ["I'm a bot, but I'm doing great!", "All systems operational!"],
    "what is your name": ["I'm ChatBot9000!", "You can call me ChatBot."],
    "bye": ["Goodbye!", "See you later!", "Take care!"]
}

def ask_chatbot(user_input):
    user_input = user_input.lower()
    for key in responses:
        if key in user_input:
            return random.choice(responses[key])
    # default response
    default_responses = [
        "Interesting! Tell me more.",
        "I see. Can you elaborate?",
        "Hmm, I am not sure about that.",
        "Let's talk about something else!"
    ]
    return random.choice(default_responses)

# Terminal loop
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Exiting chatbot. Goodbye!")
        break
    answer = ask_chatbot(user_input)
    print(f"Bot: {answer}\n")