from bson import ObjectId
from google import genai
from pydantic import BaseModel
from app.core.config import settings


class OutputFormat(BaseModel):
  related_procedures: list[str]


gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are a helpful assistant in a Retrieval-Augmented Generation (RAG) system.
Your task is to filter a list of procedures based on the USER QUERY and the dictionary of TOP-10 CANDIDATE PROCEDURES with format {{id: procedure_title}}
You need to analyze the relevance of each procedure title to the user's query and select the most relevant ones.
# NOTE: Return at most 5 IDs of procedures that are clearly relevant to the query. If fewer than 5 are clearly relevant, return fewer. If none are relevant, return an empty list.

# OUTPUT FORMAT: in JSON format:
{{ "related_procedures": ["id1", "id2", "id3"] }}

BEGIN!
"""


def filter_procedures_with_gemini(user_query, db, candidates: dict):
    user_prompt = f"""
    # USER QUERY: {user_query}
    # TOP-10 CANDIDATE PROCEDURES: {candidates}
    """
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash-lite",
        config={
        'response_mime_type': 'application/json',
        'response_schema': OutputFormat,
        "temperature": 0,
        "system_instruction": SYSTEM_PROMPT
        },
        contents=[user_prompt]
    )
    dict_response = response.parsed.__dict__

    procedure_collection = db["bocongan_detailed"]

    related_procedures_docs = procedure_collection.find({"_id": {"$in": [ObjectId(related_procedure) for related_procedure in dict_response["related_procedures"]] }})
    
    # Chuyển đổi ObjectId thành string trong kết quả
    result = []
    for doc in related_procedures_docs:
        doc['_id'] = str(doc['_id'])
        result.append(doc)
    
    return result

