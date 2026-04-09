#  TechCorp AI Assistant

A professional AI chatbot built with modern AI tools.

##  Built With
- **Groq** - LLM (llama-3.3-70b)
- **Tavily** - Real-time web search
- **RAG** - Document search with FAISS
- **MongoDB** - Conversation storage
- **LangChain** - AI framework

##  Project Structure

#  TechCorp Multi-Agent System

##  Project Overview

This project is a **Multi-Agent AI System** built using CrewAI. It intelligently handles user queries by routing them to specialized agents based on the query type.

The system integrates:

* **RAG (Retrieval-Augmented Generation)** using FAISS
* **Web Search** using Tavily API
* **MongoDB** for storing conversation history

---

##  Features

* Multi-agent architecture
* Intelligent query routing
* Real-time web search
* Document-based question answering (RAG)
* MongoDB integration for logging
* Clean and modular design

---

##  Agents & Responsibilities

### 1. Web Research Agent

* Fetches real-time information from the internet
* Handles queries like weather, news, trends

### 2. RAG (Knowledge) Agent

* Retrieves information from internal documents
* Uses FAISS for semantic search

### 3. Writer Agent

* Generates clear and structured final responses
* Ensures professional output

---

##  Project Structure

```
chatrebot/
│
├── crew_agent.py        # Main application
├── documents/           # Text files for RAG
├── faiss_index/         # Vector database (auto-generated)
├── .env                 # Environment variables
├── .gitignore           # Ignored files
└── README.md            # Project documentation
```

---

##  Setup Instructions

### 1. Clone the repository

```
git clone <your-repo-link>
cd chatrebot
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Create `.env` file

Add the following:

```
GROQ_API_KEY=your_key
TAVILY_API_KEY=your_key
MONGODB_URI=your_connection_string
```

---

##  How to Run

```
py -3.11 crew_agent.py
```

---

##  Example Queries

* What is the company leave policy?
* Who is the CEO of TechCorp?
* What is the weather in Lahore today?

---

##  Data Storage

All conversations are stored in MongoDB with:

* Question
* Answer
* Agent used
* Timestamp

---

##  Future Improvements

* Add frontend UI (Streamlit / React)
* Improve agent decision-making using AI routing
* Add memory for conversation context
* Deploy as a web application

---

##  Author

Developed as part of internship project using CrewAI and modern AI tools.