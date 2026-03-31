# chatbot_groq.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# API key loaded from .env file
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_chatbot(prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # ✅ latest working model
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

print("Welcome to Groq Terminal Chatbot! Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    answer = ask_chatbot(user_input)
    print(f"Bot: {answer}\n")