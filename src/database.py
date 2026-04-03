from pymongo import MongoClient
from datetime import datetime, timezone

def connect_mongodb(uri):
    client = MongoClient(
        uri,
        tls=True,
        tlsAllowInvalidCertificates=True
    )
    db = client["chatbot_db"]
    collection = db["conversations"]
    print("✅ MongoDB Connected!")
    return collection

def save_conversation(collection, user_id, question, answer, latency_ms, tool_used):
    record = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "latency_ms": latency_ms,
        "tool_used": tool_used,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    collection.insert_one(record)
    print(f"💾 Saved! Tool: {tool_used} | Time: {latency_ms}ms")