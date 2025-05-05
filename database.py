import re
from fuzzywuzzy import fuzz
from config import MONGO_URI, DB_NAME, USER_QUESTIONS_COLLECTION, BOT_RESPONSES_COLLECTION
import pymongo
from datetime import datetime
from Levenshtein import distance

def get_db():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db

# Lưu câu hỏi và câu trả lời vào MongoDB
def save_conversation(user_question, bot_response):
    db = get_db()
    conversation_data = {
        "Question": user_question,
        "Response": bot_response,
        "Timestamp": datetime.now()
    }
    db[USER_QUESTIONS_COLLECTION].insert_one(conversation_data)

# Lưu câu trả lời của bot
def save_bot_response(user_question, bot_response):
    db = get_db()
    response_data = {
        "Question": user_question,
        "Response": bot_response,
        "Timestamp": datetime.now()
    }
    db[BOT_RESPONSES_COLLECTION].insert_one(response_data)

#Normalize
def normalize_user_question(text):
        text = text.lower()
        text = " ".join(text.split())
        return text

#Pattern Matching 
def pattern_match(query):
    db = get_db()
    collection = db["qa_collection"]

    query = normalize_user_question(query)  

    for doc in collection.find():
        stored_question = normalize_user_question(doc["Question"]) 
        response = doc["Answer"]

        if re.search(rf"^{re.escape(stored_question)}$", query, re.IGNORECASE):
            return response

    return None

#Keyword Matching 
def keyword_match(query, min_match_ratio=0.5):
    db = get_db()
    collection = db["qa_collection"]

    query_words = set(normalize_user_question(query).split()) 
    best_match = None
    max_overlap = 0
    best_question = None

    for doc in collection.find():
        key_words = set(normalize_user_question(doc["Question"]).split())  
        overlap = len(query_words.intersection(key_words)) 

        match_ratio = overlap / len(query_words) if len(query_words) > 0 else 0  

        if match_ratio >= min_match_ratio and overlap > max_overlap:
            max_overlap = overlap
            best_match = doc["Answer"]

    if best_match is None:
        return None  

    return best_match

#Fuzzy Matching
def fuzzy_match(query, threshold=85): 
    db = get_db()
    collection = db["qa_collection"]

    query = normalize_user_question(query)  
    best_match = None
    best_score = 0

    for doc in collection.find():
        stored_question = normalize_user_question(doc["Question"])  
        score = fuzz.ratio(query, stored_question)

        if score > best_score and score >= threshold:
            best_score = score
            best_match = doc["Answer"]

    return best_match, best_score

#Levenshtein Distance
def levenshtein_match(query, threshold=3):  
    db = get_db()
    collection = db["qa_collection"]

    query = normalize_user_question(query) 
    best_match = None
    best_distance = float("inf")

    for doc in collection.find():
        stored_question = normalize_user_question(doc["Question"]) 
        dist = distance(query, stored_question)

        if dist < best_distance and dist <= threshold:
            best_distance = dist
            best_match = doc["Answer"]

    return best_match, best_distance

def calculate_similarity(user_question, stored_question):
    return fuzz.ratio(user_question, stored_question)

def find_similar_question(user_question):
    db = get_db()
    all_questions = db[USER_QUESTIONS_COLLECTION].find()
    
    best_match = None
    highest_score = 0
    # Implement tìm kiếm với fuzzy matching hoặc pattern matching
    for q in all_questions:
        score = calculate_similarity(user_question, q['Question'])  
        if score > highest_score:
            best_match = q
            highest_score = score
    return best_match

# def get_rule_base():
#     db = get_db()
#     collection = db["qa_collection"]
#     rule_base = {}
#     domain_base = {}

#     for doc in collection.find():
#         question = normalize_user_question(doc.get("Question", "").strip())
#         answer = doc.get("Answer")
#         domain = doc.get("Domain", "general") 

#         if not question or not answer:  
#             print(f"⚠️ Bỏ qua document lỗi: {doc}") 
#             continue

#         rule_base[question] = answer

#         if domain not in domain_base:
#             domain_base[domain] = []
#         domain_base[domain].append((question, answer))

#     return rule_base, domain_base

def search_rule_based(query, threshold=90):
    query = normalize_user_question(query)

    # # 1️⃣ Pattern Matching
    # match = pattern_match(query)
    # if match:
    #     return match, "pattern"
    
    # similar_question = find_similar_question(query)
    # if similar_question:
    #     best_response = similar_question['Answer']
    #     print(f"✅ Fuzzy Matching từ MongoDB tìm thấy câu trả lời: {best_response} (Độ tương đồng: {fuzz.ratio(query, similar_question['Question'])}%)")
    #     return best_response, "fuzzy-mongo"

    #2️⃣ Keyword Matching
    match = keyword_match(query)
    if match:
        return match, "keyword"
    
    # # 3️⃣ Fuzzy Matching
    # match, score = fuzzy_match(query, threshold)
    # if match:
    #     return match, "fuzzy"

    # # 4️⃣ Levenshtein Distance
    # match, dist = levenshtein_match(query)
    # if match:
    #     return match, "levenshtein"
    
    # 5️⃣ Nếu không có kết quả, tìm trong cùng Domain
    fallback_response = "Xin lỗi, tôi không thể trả lời câu hỏi này. Bạn có thể được giải đáp ở : https://support.ut.edu.vn/"
    
    return [fallback_response], "fallback"