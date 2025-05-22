from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from bson import ObjectId
from datetime import datetime, timezone

from app.core.database import get_database
from app.services.gemini import generate_response_for_procedures, filter_and_expand_query
from pydantic import BaseModel


class SentMessage(BaseModel):
    chat_id: str
    content: str
    procedures: list[dict]


class FilterAndExpandQueryRequest(BaseModel):
    chat_id: str
    content: str


router = APIRouter()


@router.post("/messages/send", response_model=dict)
def send_message(message: SentMessage, db=Depends(get_database)):
    chat_id = message.chat_id
    content = message.content
    procedures = message.procedures
    
    if content == "":
        raise HTTPException(status_code=400, detail="Content is required")

    # Get the chat
    chat = db.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    history_messages = chat["messages"]

    bot_response = generate_response_for_procedures(content, history_messages, procedures)

    # Add user message
    user_message = {
        "sender": "user",
        "text": content,
        "timestamp": datetime.now(timezone.utc)
    }

    # Add bot message
    bot_message = {
        "sender": "bot",
        "text": bot_response,
        "timestamp": datetime.now(timezone.utc)
    }

    # Update chat with new messages
    db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {"$push": {"messages": {"$each": [user_message, bot_message]}}}
    )

    return {
        "status": "success",
        "data": {
            "content": bot_response
        }
    }

@router.post("/messages/filter-and-expand-query", response_model=dict)
def filter_expand_query(message: FilterAndExpandQueryRequest, db=Depends(get_database)):
    print(message)
    chat_id = message.chat_id
    content = message.content

    # Get the chat
    chat = db.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    history_messages = chat["messages"]

    response = filter_and_expand_query(content, history_messages)

    return {
        "status": "success",
        "data": response
    }   



@router.post("/messages/resend", response_model=dict)
def resend_message(message: SentMessage, db=Depends(get_database)):
    chat_id = message.chat_id
    content = message.content

    # Get chat history
    chat = db.chats.find_one({"_id": ObjectId(chat_id)})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Remove two last messages in chat history in chat history

    # Get chat history
    history_messages = chat["messages"][:-2]
    product_information = chat["productInformation"]

    # Generate new bot response
    bot_response = generate_response_for_procedures(content, history_messages, product_information)
    bot_message = {
        "sender": "bot",
        "text": bot_response,
        "timestamp": datetime.now(timezone.utc)
    }

    user_message = {
        "sender": "user",
        "text": message.content,
        "timestamp": datetime.now(timezone.utc)
    }
    history_messages.append(user_message)
    history_messages.append(bot_message)
    
    # Update chat with new bot message
    db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"messages": history_messages}}
    )
    
    return {
        "status": "success",
        "data": {
            "content": bot_response
        }
    } 