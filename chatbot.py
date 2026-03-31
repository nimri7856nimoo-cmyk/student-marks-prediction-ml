import os
import openai

# Use your environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_chatgpt(prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"  # Catch all errors safely

print("Welcome to Terminal Chatbot! Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Exiting chatbot. Goodbye!")
        break

    answer = ask_chatgpt(user_input)
    print(f"Bot: {answer}\n")
