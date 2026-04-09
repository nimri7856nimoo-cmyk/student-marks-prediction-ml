from dotenv import load_dotenv
import os
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from pymongo import MongoClient
from datetime import datetime, timezone
import time
from langchain_tavily import TavilySearch

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

os.environ["GROQ_API_KEY"] = GROQ_API_KEY
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
os.environ["OTEL_SDK_DISABLED"] = "true"
llm = "groq/llama-3.3-70b-versatile"

#  MongoDB
client = MongoClient(MONGODB_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client["chatbot_db"]
collection = db["crew_conversations"]
print(" MongoDB Connected!")

#  Setup RAG
print(" Loading knowledge base...")
FAISS_PATH = "faiss_index"
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

if os.path.exists(FAISS_PATH):
    vectorstore = FAISS.load_local(
        FAISS_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
else:
    loader = DirectoryLoader(
        "documents",
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_PATH)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
print(" Knowledge base ready!")

#  Tavily Search
tavily_search = TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY)

#  Custom Tools
@tool("WebSearch")
def web_search(query: str) -> str:
    """Search the web for current news, weather, prices and real time information."""
    try:
        results = tavily_search.invoke(query)
        if isinstance(results, list):
            output = []
            for r in results:
                output.append(f"Title: {r.get('title','')}\nContent: {r.get('content','')}")
            return "\n\n".join(output)
        return str(results)
    except Exception as e:
        return f"Search failed: {e}"

@tool("SearchDocuments")
def search_documents(query: str) -> str:
    """Search company documents for HR policies, products and company information."""
    try:
        docs = retriever.invoke(query)
        if docs:
            return "\n\n".join([doc.page_content for doc in docs])
        return "No information found in company documents."
    except Exception as e:
        return f"Search failed: {e}"

#  Create Agents
research_agent = Agent(
    role="Web Research Specialist",
    goal="Search the web for current and accurate information",
    backstory="""You are an expert web researcher. You search the internet
    for latest news, weather updates, prices and current events.
    You always provide accurate and up to date information.""",
    tools=[web_search],
    llm=llm,
    verbose=True,
    max_iter=3
)

rag_agent = Agent(
    role="Company Knowledge Specialist",
    goal="Find accurate information from company documents",
    backstory="""You are an expert in company information. You search through
    company documents to find information about HR policies, products,
    company details and employee information.""",
    tools=[search_documents],
    llm=llm,
    verbose=True,
    max_iter=3
)

writer_agent = Agent(
    role="Professional Response Writer",
    goal="Write clear and professional responses based on research",
    backstory="""You are a professional writer who takes research results
    and writes clear, helpful and professional responses for users.
    You always write in a polite and helpful tone.""",
    tools=[],
    llm=llm,
    verbose=True,
    max_iter=3
)

#  Save to MongoDB
def save_to_mongodb(question, answer, agent_used):
    record = {
        "question": question,
        "answer": answer,
        "agent_used": agent_used,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    collection.insert_one(record)
    print(f" Saved! Agent: {agent_used}")

#  Detect which agent to use
def detect_agent(query):
    company_keywords = [
        "ceo", "company", "techcorp", "hr", "policy",
        "leave", "salary", "product", "price", "employee",
        "dress code", "working hours", "bonus", "remote",
        "contact", "email", "phone", "vision", "mission"
    ]
    query_lower = query.lower()
    for keyword in company_keywords:
        if keyword in query_lower:
            return "RAG"
    return "WEB"

#  Check greetings
def is_greeting(query):
    greetings = [
        "hello", "hi", "hey", "how are you",
        "good morning", "good evening", "good night",
        "salam", "assalam", "whats up", "what's up"
    ]
    query_lower = query.lower().strip()
    return any(g in query_lower for g in greetings)

#  Run Crew
def run_crew(question):
    agent_type = detect_agent(question)

    if agent_type == "RAG":
        # ✅ Search documents ourselves first
        pre_search = search_documents.run(question)
        
        research_task = Task(
            description=f"""Here is the relevant information from company documents:

{pre_search}

Based on this information, answer this question: {question}""",
            expected_output="A clear answer based on the provided company information",
            agent=rag_agent
        )
        agent_used = "RAG Agent"
        active_agents = [rag_agent, writer_agent]
    else:
        # ✅ Search web ourselves first
        pre_search = web_search.run(question)
        
        research_task = Task(
            description=f"""Here is the relevant information from web search:

{pre_search}

Based on this information, answer this question: {question}""",
            expected_output="A clear answer based on the web search results",
            agent=research_agent
        )
        agent_used = "Web Research Agent"
        active_agents = [research_agent, writer_agent]

    write_task = Task(
        description=f"""Based on the research results, write a clear and
        professional response to this question: {question}""",
        expected_output="A clear, professional and helpful response",
        agent=writer_agent
    )

    crew = Crew(
        agents=active_agents,
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    return str(result), agent_used

#  Main Chat Loop
print("\n" + "="*50)
print("    TechCorp Multi-Agent System")
print("="*50 + "\n")

while True:
    query = input("You: ")

    if query.lower() == "exit":
        print("\nGoodbye! \n")
        break

    if query.strip() == "":
        continue

    if is_greeting(query):
        print("\n AI: Hello! Welcome to TechCorp AI Assistant. How can I help you today?\n")
        continue

    try:
        print("\n Agents working...\n")
        start_time = time.time()
        answer, agent_used = run_crew(query)
        latency = int((time.time() - start_time) * 1000)
        save_to_mongodb(query, answer, agent_used)
        print(f"\n Final Answer: {answer}")
        print(f"⏱ Time: {latency}ms\n")

    except Exception as e:
        print(f" Error: {e}\n")