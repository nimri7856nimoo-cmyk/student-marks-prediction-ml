from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class QueryRequest(BaseModel):
    question: str


# ================= IMPORTS =================
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

# ================= MONGODB =================
client = MongoClient(MONGODB_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client["chatbot_db"]
collection = db["crew_conversations"]

# ================= RAG =================
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
    loader = DirectoryLoader("documents", glob="**/*.txt", loader_cls=TextLoader)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_PATH)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ================= TAVILY =================
tavily_search = TavilySearch(max_results=3, tavily_api_key=TAVILY_API_KEY)

# ================= TOOLS =================
@tool("WebSearch")
def web_search(query: str) -> str:
    """Search the web for real-time information like news, weather, etc."""
    try:
        results = tavily_search.invoke(query)
        if isinstance(results, list):
            return "\n\n".join(
                [f"Title: {r.get('title','')}\nContent: {r.get('content','')}" for r in results]
            )
        return str(results)
    except Exception as e:
        return f"Search failed: {e}"

@tool("SearchDocuments")
def search_documents(query: str) -> str:
    """Search internal company documents using RAG."""
    try:
        docs = retriever.invoke(query)
        if docs:
            return "\n\n".join([doc.page_content for doc in docs])
        return "No information found."
    except Exception as e:
        return f"Search failed: {e}"

# ================= AGENTS =================
research_agent = Agent(
    role="Web Research Specialist",
    goal="Search web for current information",
    backstory="Expert web researcher",
    tools=[web_search],
    llm=llm,
    verbose=False
)

rag_agent = Agent(
    role="Company Knowledge Specialist",
    goal="Answer from company documents",
    backstory="Expert in company data",
    tools=[search_documents],
    llm=llm,
    verbose=False
)

writer_agent = Agent(
    role="Professional Writer",
    goal="Write clear responses",
    backstory="Professional assistant",
    tools=[],
    llm=llm,
    verbose=False
)

# ================= HELPER FUNCTIONS =================
def save_to_mongodb(question, answer, agent_used):
    collection.insert_one({
        "question": question,
        "answer": answer,
        "agent_used": agent_used,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

def detect_agent(query):
    keywords = ["ceo","company","hr","policy","leave","salary","product"]
    return "RAG" if any(k in query.lower() for k in keywords) else "WEB"

def run_crew(question):
    agent_type = detect_agent(question)

    if agent_type == "RAG":
        pre_search = search_documents.run(question)
        agent_used = "RAG Agent"
        active_agents = [rag_agent, writer_agent]
    else:
        pre_search = web_search.run(question)
        agent_used = "Web Agent"
        active_agents = [research_agent, writer_agent]

    research_task = Task(
        description=f"{pre_search}\n\nAnswer: {question}",
        expected_output="Clear answer",
        agent=active_agents[0]
    )

    write_task = Task(
        description=f"Write professional answer for: {question}",
        expected_output="Final answer",
        agent=writer_agent
    )

    crew = Crew(
        agents=active_agents,
        tasks=[research_task, write_task],
        process=Process.sequential,
        verbose=False
    )

    result = crew.kickoff()
    return str(result), agent_used

# ================= FASTAPI ROUTES =================
@app.get("/")
def home():
    return {"message": "CrewAI FastAPI Running 🚀"}

@app.post("/chat")
def chat(req: QueryRequest):
    try:
        start_time = time.time()

        answer, agent_used = run_crew(req.question)

        latency = int((time.time() - start_time) * 1000)

        save_to_mongodb(req.question, answer, agent_used)

        return {
            "question": req.question,
            "answer": answer,
            "agent": agent_used,
            "latency_ms": latency
        }

    except Exception as e:
        return {"error": str(e)}