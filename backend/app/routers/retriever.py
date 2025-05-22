from fastapi import APIRouter, HTTPException, Depends
from app.core.database import get_database
from pydantic import BaseModel
from app.retriever_services.retriever import retrieve_procedures


router = APIRouter()


class RetrieveRequest(BaseModel):
    query: str


@router.post("/retrieve", response_model=dict)
def retrieve(request: RetrieveRequest, db=Depends(get_database)):
    procedures = retrieve_procedures(request.query, db)
    return {"procedures": procedures}
