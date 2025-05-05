import uvicorn
from fastapi import FastAPI
from session_manager import chat_with_user
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI()

class ChatRequest(BaseModel):
    userId: str
    inputQuestion: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(inputData: ChatRequest):
    user_id = inputData.userId
    user_question = inputData.inputQuestion

    if not user_question:
        return ChatResponse(response="Thiếu inputQuestion")

    response_data = chat_with_user(user_id, user_question)  
    
    return ChatResponse(response=response_data["response"]) 

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7979)
