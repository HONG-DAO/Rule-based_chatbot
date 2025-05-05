import uuid
from session_manager import chat_with_user, suggest_questions
import json
import os

SESSION_FILE = "session.json"  

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            return data.get("session_id", str(uuid.uuid4()))
    return str(uuid.uuid4())

def save_session(session_id):
    with open(SESSION_FILE, "w") as f:
        json.dump({"session_id": session_id}, f)

def start_chat():
    user_id = load_session()
    save_session(user_id)
    print(f"🔹 Session ID của bạn: {user_id}")

    suggestions = suggest_questions(user_id)
    if suggestions:
        print("\n💡 Gợi ý câu hỏi phổ biến:")
        for i, q in enumerate(suggestions, 1):
            print(f"{i}. {q}")

    while True:
        query = input("\n👤 Bạn: ").strip()
        if query.lower() in ["exit", "quit", "bye"]:
            print("\n🚪 Đã kết thúc cuộc trò chuyện!")
            break

        response = chat_with_user(user_id, query)
        print(f"\n🤖 Bot: {response}")

if __name__ == "__main__":
    start_chat()

