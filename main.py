import os
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from ai.gemini import Gemini
from dependencies import get_user_identifier
from throttling import apply_rate_limit
from typing import Optional, Dict, Any
import sys 
import time
import dotenv
# from gemini import Gemini

dotenv.load_dotenv()


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
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("Your environment variable not set.")

ai_platform = Gemini(api_key=gemini_api_key, system_prompt=system_prompt)


#--- Pydantic Models ---
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


#--- API Endpoints ---
# @workoutApp.post("/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest, user_id: str = Depends(get_user_identifier)):
#     apply_rate_limit(user_id)
#     response_text = ai_platform.chat(request.prompt)
#     return ChatResponse(response=response_text)

@workoutApp.post("/generate-workout")
async def generate_workout(request: WorkoutPlanRequest, user_id: str = Depends(get_user_identifier)):
    apply_rate_limit(user_id)
    plan = ai_platform.workoutPlanChatBot(request.Dict[str, Any]())
    return {"workout_plan": plan}


@workoutApp.get("/")
async def root():
    return {"message": "API is running"}

def testVoice(gemini_instance):
    #testing a couple of the voices for our gemini workout partner
    print("Testing Voice Tone")

    #Test prompts designed for each tone
    tone_tests = {
        "neutral": [
            "Good morning, how can I help you today?",
            "Please explain the weather forecast",
            "What are the benefits of reading books?"
        ],
        "gymbro": [
            "Tell me about building muscle and getting swole!",
            "What's the best pre-workout motivation?",
            "How do I crush my fitness goals this week?"
        ],
        "girly": [
            "What are some cute self-care ideas?",
            "Tell me about your favorite skincare routine",
            "How can I make my day more sparkly and fun?"
        ]
    }
    for tone, prompts in tone_tests.items():
        print(f"🗣️ Testing {tone.upper()} tone:")
        for i, prompt in enumerate(prompts, 1):
            try:
                print(f"  Test {i}: {prompt}")
                # Test with async speech (won't block)
                response = gemini_instance.voiceToneOutput(prompt, tone=tone, speak_async=True)
                print(f"  Response: {response}")
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                print(f"   Error in {tone} tone test {i}: {e}")
        print()
    def test_voice_setup(gemini_instance):
        """Test voice profile setup"""
        print("🔧 Testing Voice Profile Setup...")
        print("-" * 50)
    
        try:
            # This should print available voices
            gemini_instance.setUpVoiceProfiles()
            print("✅ Voice profiles setup completed")
        except Exception as e:
            print(f"Voice setup error: {e}")
    
        print()
    def main():
        print("Start tests")
        try:
            # Test 1: Voice Setup
            test_voice_setup(ai_platform)
        
            # Test 2: Basic Chat
            #test_basic_chat(ai_platform)
        
            # Test 3: Voice Tones
            testVoice(ai_platform)
        
            print(" All tests completed successfully!")
        except KeyboardInterrupt:
            print("\n Tests interrupted by user")
        except Exception as e:
            print(f"\n Test execution failed: {e}")
        