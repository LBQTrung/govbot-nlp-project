from google import genai
from app.core.config import settings
from typing import List, Dict
from pydantic import BaseModel


class FilterAndExpandQueryResponse(BaseModel):
    has_enough_context: bool
    response: str


# Configure Gemini
def generate_chat_name(user_message: str, bot_response: str) -> str:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt = f"""
        Generate a short, descriptive name (max 5 words) for a chat based on the following conversation and contextual information. 
        The name should reflect the main topic or purpose of the conversation. 
        Conversation:
        User: {user_message}
        Bot: {bot_response}
    """
    
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[
            prompt,
        ],
        config={
            "temperature": 0,
            "system_instruction": prompt
        }
    )
    return response.text.strip()

def filter_and_expand_query(message: str, history_messages: list) -> str:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    SYSTEM_PROMPT = f"""
You are a language model designed to analyze user queries based on previous conversation history in order to ensure appropriate classification and response generation.

Your tasks:
- Evaluate whether the current query, combined with the previous conversation, forms a complete question with sufficient context about a public administrative procedure.
- If it does form a complete administrative procedure question, rewrite the current query into a fully contextualized and self-contained question.
- If it forms a complete question but is not related to public administrative procedures, respond to the user accordingly (as a general assistant).
- If the current query and the previous conversation do not form a complete question about an administrative procedure, ask a clarifying question to the user to obtain the missing context.
{{
  "has_enough_context": <true_or_false>,
  "response": "<the completed query about the public administrative procedure, or an appropriate response for non-administrative topics, or a clarifying question if the context is insufficient>"
}}

IMPORTANT: Always respond in the same language as the user's input
"""
    

    # Format chat history
    history_text = "\n".join([
        f"{msg['sender']}: {msg['text']}"
        for msg in history_messages[-5:]  # Only use last 5 messages for context
    ])
    
    user_prompt = f"""
PREVIOUS CONVERSATION:
{history_text}

CURRENT USER QUESTION: {message}

ASSISTANT:"""
    
    
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[
            user_prompt,
        ],
        config={
            "temperature": 0,
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": FilterAndExpandQueryResponse
        }
    )
    return response.parsed.__dict__



def generate_response_for_procedures(message: str, history_messages: list, procedures: list[dict]) -> str:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    SYSTEM_PROMPT = f"""
You are an AI assistant designed to support users with public administrative procedures, using only information from the PREVIOUS CONVERSATION (history message) and the RELEVANT PROCEDURES to answer user questions.

Your responsibilities:
- Use only the conversation history and the provided procedure data to generate accurate, relevant, and helpful responses.
- Present information clearly, using:
    - Bullet points for general details;
    - Numbered lists for procedural steps.
- Maintain a friendly, natural tone that aligns with the previous conversation.
- Do not use outside knowledge or make assumptions beyond the given procedures and message history.
- If the required information is not available, respond with:
    "Sorry, I currently do not have enough information to answer that question."

IMPORTANT: Always respond in the same language as the user's input    
"""
    

    # Format chat history
    history_text = "\n".join([
        f"{msg['sender']}: {msg['text']}"
        for msg in history_messages[-5:]  # Only use last 5 messages for context
    ])
    
    user_prompt = f"""
RELEVANT PROCEDURES:
{procedures}

PREVIOUS CONVERSATION:
{history_text}

USER QUESTION: {message}

ASSISTANT:"""
    
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=[
            user_prompt,
        ],
        config={
            "temperature": 0,
            "system_instruction": SYSTEM_PROMPT
        }
    )
    return response.text.strip() 