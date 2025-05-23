from google import genai
from app.core.config import settings
from typing import List, Dict
from pydantic import BaseModel


class ExtractUserMessageResponse(BaseModel):
    procedure_name: str | None
    problem: str | None


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


def extract_user_message(message: str, history_messages: list) -> str:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    SYSTEM_PROMPT = f"""
You are an assistant designed to extract structured information from a conversation related to public administrative procedures.

Your Task:
Given:
- The **CURRENT USER QUESTION**.
- The **PREVIOUS CONVERSATION**.

Determine whether the user has provided:
1. The **name of the public administrative procedure** (e.g., "đăng ký khai sinh", "gia hạn giấy phép kinh doanh").
2. The **specific problem or question** they have about this procedure (e.g., "cần giấy tờ gì", "mất bao lâu").

Focus on the **most recent parts of the conversation**, especially the latest messages, to ensure you are capturing the user's current intent, in case they have changed the topic or are asking about a different procedure than before.

If both pieces of information are available, return the result in the following JSON format, with all **values in Vietnamese**:
{{
  "procedure_name": "tên thủ tục hành chính bằng tiếng Việt",
  "problem": "vấn đề cụ thể mà người dùng hỏi, bằng tiếng Việt"
}}

If either procedure_name or problem is missing, return:
{{
  "procedure_name": None,
  "problem": None
}}
"""
    history_text = "\n".join([
        f"{msg['sender']}: {msg['text']}"
        for msg in history_messages  # Only use last 5 messages for context
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
            "response_schema": ExtractUserMessageResponse
        }
    )
    return response.parsed.__dict__



def basic_question_generator(message: str, history_messages: list) -> str:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    SYSTEM_PROMPT = f"""
You are an assistant that helps users inquire about public administrative procedures.

Your Task:
Based on the following extracted JSON:
{{
  "procedure_name": "tên thủ tục hành chính bằng tiếng Việt",
  "problem": "vấn đề cụ thể mà người dùng hỏi, bằng tiếng Việt"
}}

If any of the fields (procedure_name, problem) are null or missing, generate a natural, polite question in Vietnamese to ask the user for the missing information. The goal is to collect the minimal necessary details so that we can answer their question correctly.
Guidelines:
- Ask for only the missing information.
- If both fields are missing, ask a question that guides the user to provide both.
- Your question must be clear, concise, and in Vietnamese.
- Do not repeat information already provided.
- Do not assume anything beyond what's given.

Examples:

If "procedure_name": null, "problem": "Tôi cần biết mất bao lâu"
→ Ask: "Bạn đang hỏi về thủ tục hành chính nào vậy ạ?"

If "procedure_name": "Đăng ký kết hôn", "problem": null
→ Ask: "Bạn cần hỏi gì về thủ tục 'Đăng ký kết hôn' ạ?"

If both are null
→ Ask: "Bạn vui lòng cho biết bạn đang hỏi về thủ tục hành chính nào và bạn đang cần hỗ trợ vấn đề gì ạ?"

"""
    

    # Format chat history
    history_text = "\n".join([
        f"{msg['sender']}: {msg['text']}"
        for msg in history_messages  # Only use last 5 messages for context
    ])

    print(history_text)
    
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
            "temperature": 0.7,
            "system_instruction": SYSTEM_PROMPT,
        }
    )
    return response.text.strip()



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