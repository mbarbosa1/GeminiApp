import os
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from .ai.gemini import Gemini
from dependencies import get_user_identifier
from throttling import apply_rate_limit
GLOBAL_RATE_LIMIT = 3
GLOBAL_TIME_WINDOW_SECONDS = 60

#--- App Initialization ---
workoutApp = FastAPI()


#--- AI Configuration ---
def load_system_prompt():
    try:
        with open("src/prompts/system_prompt.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


system_prompt = load_system_prompt()
gemini_api_key = os.getenv("AIzaSyACJmac54quT2vGe4urNWlzwku3dkh6oxg")

if not gemini_api_key:
    raise ValueError("AIzaSyACJmac54quT2vGe4urNWlzwku3dkh6oxg environment variable not set.")

ai_platform = Gemini(api_key=AIzaSyACJmac54quT2vGe4urNWlzwku3dkh6oxg, system_prompt=system_prompt)


#--- Pydantic Models ---
class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


#--- API Endpoints ---
@workoutApp.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user_id: str = Depends(get_user_identifier)):
    apply_rate_limit(user_id)
    response_text = ai_platform.chat(request.prompt)
    return ChatResponse(response=response_text)


@app.get("/")
async def root():
    return {"message": "API is running"}
