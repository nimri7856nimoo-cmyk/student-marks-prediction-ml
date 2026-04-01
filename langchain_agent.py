from dotenv import load_dotenv
import os
import time
import ssl
from datetime import datetime, timezone

from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from pymongo import MongoClient

#  Load API keys
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

#  SSL fix for Python 3.14
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

#  Connect to MongoDB
client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsAllowInvalidCertificates=True
)
db = client["chatbot_db"]
collection = db["conversations"]
print(" MongoDB Connected!")

#  Setup Groq LLM
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=GROQ_API_KEY
)

#  Setup Tavily Search Tool
search_tool = TavilySearch(
    max_results=3,
    tavily_api_key=TAVILY_API_KEY
)

tools = [search_tool]

#  System Prompt
system_prompt = """You are a helpful AI assistant with access to web search tool.

IMPORTANT RULES:
- ALWAYS use the tavily search tool first before answering ANY question
- NEVER answer from your own knowledge without searching
- For weather questions, search specifically: "weather in [city] today site:weather.com OR site:accuweather.com"
- Always mention the exact temperature, humidity, and condition from search results
- For news, ALWAYS search for latest updates
- Only give answers based on what you find in search results
- If first search result seems outdated, search again with different keywords

You must search first, then answer with EXACT data from search results!"""

agent = create_react_agent(llm, tools, prompt=system_prompt)

#  Check if Tavily was used
def check_tool_used(response):
    for message in response["messages"]:
        if hasattr(message, "name") and message.name == "tavily_search_results_json":
            return "Tavily"
    return "None"

#  Save to MongoDB
def save_to_mongodb(user_id, question, answer, latency_ms, tool_used):
    record = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "latency_ms": latency_ms,
        "tool_used": tool_used,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    collection.insert_one(record)
    print(f"💾 Saved to MongoDB! Tool used: {tool_used} | Time: {latency_ms}ms")

#  Chat Loop
print("\n🤖 AI Agent with Web Search ready! (type 'exit' to quit)\n")

user_id = "user_001"

while True:
    query = input("You: ")

    if query.lower() == "exit":
        print("Goodbye!")
        break

    if query.strip() == "":
        continue

    try:
        start_time = time.time()

        response = agent.invoke(
            {"messages": [HumanMessage(content=query)]}
        )

        latency_ms = int((time.time() - start_time) * 1000)
        final_answer = response["messages"][-1].content
        tool_used = check_tool_used(response)

        save_to_mongodb(user_id, query, final_answer, latency_ms, tool_used)

        print(f"\nAI: {final_answer}\n")

    except Exception as e:
        print(f"Error: {e}\n")