from dotenv import load_dotenv
import os
import time
import sys
from langchain_core.messages import HumanMessage

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.database import connect_mongodb, save_conversation
from src.rag import setup_vectorstore, create_rag_tool
from src.agent import setup_agent, check_tool_used

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

print("\n" + "="*50)
print("    TechCorp AI Assistant - Professional")
print("="*50 + "\n")

collection = connect_mongodb(MONGODB_URI)
retriever = setup_vectorstore()
rag_tool = create_rag_tool(retriever)
agent = setup_agent(GROQ_API_KEY, TAVILY_API_KEY, rag_tool)

print("\n" + "="*50)
print("   Ready! Type your question or exit to quit")
print("="*50 + "\n")

user_id = "user_001"

while True:
    query = input("You: ")

    if query.lower() == "exit":
        print("\nGoodbye! Have a great day! \n")
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
        save_conversation(
            collection, user_id, query,
            final_answer, latency_ms, tool_used
        )
        print(f"\n AI: {final_answer}\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")