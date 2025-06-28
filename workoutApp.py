import os
import io
import time
from typing import Optional, Dict, Any

from fastapi import Depends, FastAPI, File, UploadFile  # ← added UploadFile, File
from fastapi.middleware.cors import CORSMiddleware       # ← added CORS middleware
from pydantic import BaseModel
from PIL import Image                                    # ← for image preprocessing
import numpy as np                                       # ← for array handling
import tensorflow as tf                                  # ← for TFLite Interpreter

from ai.gemini import Gemini
from dependencies import get_user_identifier
from throttling import apply_rate_limit
import dotenv

dotenv.load_dotenv()

#── Global rate-limit settings ────────────────────────────────────────────────
GLOBAL_RATE_LIMIT = 3
GLOBAL_TIME_WINDOW_SECONDS = 60

#── App Initialization ────────────────────────────────────────────────────────
workoutApp = FastAPI()


workoutApp.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],  # during dev; tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

#── AI Configuration (your existing Gemini setup) ──────────────────────────────
def load_system_prompt():
    try:
        with open("src/prompts/system_prompt.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return None

system_prompt = load_system_prompt()
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("Your environment variable not set.")

ai_platform = Gemini(api_key=gemini_api_key, system_prompt=system_prompt)

#── TFLite Model Setup ────────────────────────────────────────────────────────
# These globals will hold your loaded TFLite interpreter and I/O details
interpreter = None
input_details = None
output_details = None

@workoutApp.on_event("startup")
def load_tflite_model():
    global interpreter, input_details, output_details
    # Replace "model.tflite" with the path to your .tflite file
    interpreter = tf.lite.Interpreter(model_path="model.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print(" TFLite model loaded and ready.")

#── Pydantic Models (your existing ones) ───────────────────────────────────────
class WorkoutPlanRequest(BaseModel):
    name: Optional[str] = "User"
    gender: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    goal: str
    fitness_level: str
    available_equipment: Optional[str] = "Bodyweight only"
    available_time_per_session: str
    days_per_week: int
    target_muscle_groups: Optional[str] = "Full Body"
    limitations: Optional[str] = "None specified"
    experience_level: Optional[str] = "Beginner"

class ChatResponse(BaseModel):
    response: str

#── Your Existing Endpoints ────────────────────────────────────────────────────
@workoutApp.post("/generate-workout")
async def generate_workout(request: WorkoutPlanRequest,
                           user_id: str = Depends(get_user_identifier)):
    apply_rate_limit(user_id)
    plan = ai_platform.workoutPlanChatBot(request.Dict[str, Any]())
    return {"workout_plan": plan}

@workoutApp.get("/")
async def root():
    return {"message": "API is running"}

#── New Inference Endpoint ─────────────────────────────────────────────────────
@workoutApp.post("/predict/")
async def predict(file: UploadFile = File(...),
                  user_id: str = Depends(get_user_identifier)):
    """
    Accepts a JPEG/PNG frame upload from the front end,
    runs it through your TFLite model, and returns JSON.
    """
    apply_rate_limit(user_id)

    # 1. Read bytes and open with PIL
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    # 2. Resize & normalize to match model's expected shape
    target_h = input_details[0]["shape"][1]
    target_w = input_details[0]["shape"][2]
    image = image.resize((target_w, target_h))
    input_tensor = np.expand_dims(np.array(image) / 255.0, axis=0).astype(np.float32)

    # 3. Run inference
    interpreter.set_tensor(input_details[0]["index"], input_tensor)
    interpreter.invoke()
    preds = interpreter.get_tensor(output_details[0]["index"])

    # 4. Return as Python list → JSON
    return {"predictions": preds.tolist()}

#── (Optional) Test functions & entrypoint ──────────────────────────────────────
def testVoice(gemini_instance):
    # … your existing tests …
    pass

def main():
    print("Start tests")
    try:
        testVoice(ai_platform)
        print("All tests completed successfully!")
    except Exception as e:
        print(f"Test execution failed: {e}")

if __name__ == "__main__":
    main()