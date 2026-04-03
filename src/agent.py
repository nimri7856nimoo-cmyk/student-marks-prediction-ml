from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent

SYSTEM_PROMPT = """You are a helpful AI assistant for TechCorp Pakistan.

You have two tools available:
1. search_knowledge_base: use this for company questions
2. tavily_search: use this for weather and news

IMPORTANT RULES:
- For greetings like "hello", "hi", "how are you", "good morning" — answer directly WITHOUT using any tool
- For small talk and general conversation — answer directly WITHOUT using any tool  
- For company questions like CEO, HR policy, products — use search_knowledge_base
- For weather, news, prices — use tavily_search
- NEVER use tavily for simple greetings or conversation

Be polite and professional!"""

def setup_agent(groq_api_key, tavily_api_key, rag_tool):
    llm = ChatGroq(
        temperature=0,
        model_name="llama-3.3-70b-versatile",
        groq_api_key=groq_api_key,
        model_kwargs={"parallel_tool_calls": False}
    )
    search_tool = TavilySearch(
        max_results=5,
        tavily_api_key=tavily_api_key
    )
    tools = [rag_tool, search_tool]
    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    print("✅ AI Agent Ready!")
    return agent

def check_tool_used(response):
    for message in response["messages"]:
        if hasattr(message, "name") and message.name is not None:
            if "knowledge" in str(message.name).lower():
                return "RAG"
            if "tavily" in str(message.name).lower():
                return "Tavily"
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                if "knowledge" in str(tool_call).lower():
                    return "RAG"
                if "tavily" in str(tool_call).lower():
                    return "Tavily"
    return "None"
