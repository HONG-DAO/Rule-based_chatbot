from database import get_db, search_rule_based, fuzzy_match
from datetime import datetime

def save_conversation(user_id, user_question, bot_response, domain=None):
    db = get_db()
    collection = db["user_questions"]

    existing_entry = collection.find_one({"UserID": user_id, "Question": user_question})
    
    if existing_entry:
        collection.update_one(
            {"_id": existing_entry["_id"]},
            {"$set": {"Response": bot_response, "Timestamp": datetime.now()}}
        )
    else:
        conversation_data = {
            "UserID": user_id,
            "Question": user_question,
            "Response": bot_response,
            "Domain": domain,
            "Timestamp": datetime.now()
        }
        collection.insert_one(conversation_data)

def suggest_questions(user_id, num_suggestions=3):
    db = get_db()
    collection = db["user_questions"]

    user_conversations = list(collection.find({"UserID": user_id}))
    if not user_conversations:
        top_questions = collection.aggregate([
            {"$group": {"_id": "$Question", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": num_suggestions}
        ])
        return [q["_id"] for q in top_questions]

    last_question = user_conversations[-1]["Question"]
    
    best_match, score = fuzzy_match(last_question, threshold=70)

    if best_match and score >= 70:
        return [best_match]
    return []

def generate_fallback_response(user_id, query):
    related_questions = suggest_questions(user_id, num_suggestions=2)

    if related_questions:
        return (
            "Xin lỗi, tôi chưa có câu trả lời cho câu hỏi này. "
            "Bạn có thể thử hỏi những câu sau:\n" +
            "\n".join([f"- {q}" for q in related_questions])
        )
    
    return "Xin lỗi, tôi không thể trả lời câu hỏi này ngay bây giờ. Bạn có thể tham khảo thêm tại: https://support.ut.edu.vn/"

feedback_store = {}

def chat_with_user(user_id, query):
    responses, method = search_rule_based(query)

    if responses:
        best_response = responses if isinstance(responses, str) else responses[0]
        save_conversation(user_id, query, best_response)

        feedback_store[user_id] = {"query": query, "responses": responses, "index": 0}

        return {"response": best_response.strip()}  

    fallback_response = generate_fallback_response(user_id, query)
    save_conversation(user_id, query, fallback_response)

    feedback_store[user_id] = {"query": query, "responses": [fallback_response], "index": 0}

    return {"response": fallback_response.strip()}
