from fastapi import APIRouter, HTTPException, Depends
from typing import List
from bson import ObjectId
from datetime import datetime

from app.models.chat import ChatCreate, ChatUpdate
from app.core.database import get_database
from app.services.gemini import generate_chat_name

router = APIRouter()

@router.post("/chat", response_model=dict)
def create_chat(chat: ChatCreate, db=Depends(get_database)):
    chat_dict = chat.model_dump()
    print(chat_dict)
    chat_dict["userId"] = "user123"  # In a real app, this would come from authentication
    chat_dict["createdAt"] = datetime.now().replace(microsecond=0).isoformat()
    chat_dict["name"] = "New Chat" 
    
    result = db.chats.insert_one(chat_dict)
    chat_dict["_id"] = str(result.inserted_id)
    
    return {"status": "success", "data": chat_dict}


@router.get("/chats", response_model=dict)
def get_chats(db=Depends(get_database)):
    chats = []
    for chat in db.chats.find().sort("createdAt", -1):  # Changed to -1 for descending order (newest first)
        chat["_id"] = str(chat["_id"])
        chats.append(chat)
    
    return {"status": "success", "data": chats}

 
@router.get("/chats/{chat_id}", response_model=dict)
def get_chat(chat_id: str, db=Depends(get_database)):
    chat = db.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat["_id"] = str(chat["_id"])
    return {"status": "success", "data": chat}


@router.patch("/chats/{chat_id}/rename", response_model=dict)
def rename_chat(chat_id: str, chat_update: ChatUpdate, db=Depends(get_database)):
    if not chat_update.name:
        raise HTTPException(status_code=400, detail="New chat name is required")
    
    # Get the chat
    chat = db.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Update the chat name
    result = db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"name": chat_update.name}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {"status": "success", "message": "Chat renamed successfully"}


@router.delete("/chats/{chat_id}", response_model=dict)
def delete_chat(chat_id: str, db=Depends(get_database)):
    result = db.chats.delete_one({"_id": ObjectId(chat_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {"status": "success", "message": "Chat deleted successfully"}


@router.get("/chats/{chat_id}/get-name", response_model=dict)
def get_chat_name(chat_id: str, db=Depends(get_database)):
    chat = db.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get the first user message and bot response
    messages = chat.get("messages", [])
    if len(messages) < 2:
        raise HTTPException(status_code=400, detail="Need at least one user message and one bot response")
    
    first_user_message = None
    first_bot_response = None
    
    for msg in messages:
        if msg["sender"] == "user" and first_user_message is None:
            first_user_message = msg["text"]
        elif msg["sender"] == "bot" and first_bot_response is None:
            first_bot_response = msg["text"]
        
        if first_user_message and first_bot_response:
            break
    
    if not first_user_message or not first_bot_response:
        raise HTTPException(status_code=400, detail="Could not find both user message and bot response")
    
    # Generate chat name using Gemini
    chat_name = generate_chat_name(first_user_message, first_bot_response)
    
    return {"status": "success", "data": {"chatName": chat_name}}