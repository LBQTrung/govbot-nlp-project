from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import chat, messages, retriever
from app.core.config import settings
from app.core.database import connect_to_mongo
import uvicorn
import os

app = FastAPI(title="Chatbot API")

# Create uploads directory if it doesn't exist
os.makedirs("static/uploads", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to MongoDB
app.add_event_handler("startup", connect_to_mongo)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(messages.router, prefix="/api", tags=["messages"])
app.include_router(retriever.router, prefix="/api", tags=["retriever"])

@app.get("/")
def root():
    return {"message": "Welcome to Chatbot API"}

if __name__ == "__main__":
    print("\n🚀 Starting FastAPI server...")
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
