import os
import google.generativeai as genai
from .base import AIPlatform
import time
import json
from typing import Dict, List, Optional, Any
# from google.cloud import texttospeech
import pyttsx3
import threading


class Gemini(AIPlatform):
    def __init__(self, api_key: str, system_prompt: str = None):
        self.api_key = api_key
        self.system_prompt = system_prompt
        genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

        # self.textToSpeechClient = texttospeech.TextToSpeechClient()
        self.tts_engine = pyttsx3.init()
        self.setUpVoiceProfiles()

    def chat(self, prompt: str) -> str:
        if self.system_prompt:
            prompt = f"{self.system_prompt}\n\n{prompt}"

        response = self.model.generate_content(prompt)
        return response.text
    # def voiceToneOutput(self, input):
    #     # textToSpeech
    #     # Gemini (text generation) → pyttsx3

    def voiceToneOutput(self, prompt: str, tone: str = "neutral", speak_async: bool = True) -> str:
        """
        Generate text response and convert to speech with specified tone
        Args:
        prompt (str): The input prompt for text generation
        tone (str): Voice tone - 'neutral', 'gymbro', or 'girly'
        speak_async (bool): Whether to speak in background thread
    
        Returns:
        str: The generated text response
        """
        text_response = self.chat(prompt)
        # Get voice profile for the specified tone
        profile = self.voice_profiles.get(tone.lower(), self.voice_profiles["neutral"])
    
        # Configure TTS engine with the profile settings
        self._configure_voice(profile)
    
        # Speak the text (async or sync)
        if speak_async:
            threading.Thread(
                target=self._speak_text, 
                args=(text_response,), 
                daemon=True
            ).start()
        else:
            self._speak_text(text_response)
    
        return text_response

        #using google cloud, last resort since w e have to pay
        # # Choose voice/tone
        # voice_params = {
        #     "neutral": {"language_code": "en-US", "name": "en-US-Wavenet-D"},
        #     "gymbro": {"language_code": "en-US", "name": "en-US-Wavenet-B"},
        #     "girly": {"language_code": "en-US", "name": "en-US-Wavenet-C"},
        # }
        # voice = voice_params.get(tone.lower(), voice_params["neutral"])

        # synthesis_input = texttospeech.SynthesisInput(text=text_response)
        # voice_config = texttospeech.VoiceSelectionParams(
        #     language_code=voice["language_code"],
        #     name=voice["name"]
        # )
        # audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        # response = self.tts_client.synthesize_speech(
        #     input=synthesis_input,
        #     voice=voice_config,
        #     audio_config=audio_config
        # )

        # return response.audio_content  # MP3 audio bytes
    def chooseVoice(self, profile: dict):
        voices = self.tts_engine.getProperty('voices')

        #setting a voice
        voices = self.tts_engine.getProperty('voices')
    
        # Set voice (if available)
        if profile["voice_index"] < len(voices):
            self.tts_engine.setProperty('voice', voices[profile["voice_index"]].id)
    
        # Set speech rate (words per minute)
        self.tts_engine.setProperty('rate', profile["rate"])
    
        # Set volume (0.0 to 1.0)
        self.tts_engine.setProperty('volume', profile["volume"])
    

    def setUpVoiceProfiles(self):
        voices = self.tts_engine.getProperty('voices')
    
        # Define voice configurations for each tone
        self.voice_profiles = {
            "neutral": {
                "voice_index": 0,  # Usually default system voice
                "rate": 180,       # Normal speaking speed
                "volume": 0.8,     # Normal volume
                "pitch": 0         # Default pitch (if supported)
            },
            "gymbro": {
                "voice_index": 0,  # Prefer male voice if available
                "rate": 220,       # Faster, more energetic
                "volume": 0.95,    # Louder, more assertive
                "pitch": -10       # Slightly lower pitch (if supported)
            },
            "girly": {
                "voice_index": 1 if len(voices) > 1 else 0,  # Prefer female voice
                "rate": 160,       # Slightly slower, more gentle
                "volume": 0.7,     # Softer volume
                "pitch": 10        # Higher pitch (if supported)
            }
        }
    
        # Print available voices for debugging
        # print("Available TTS voices:")
        # for i, voice in enumerate(voices):
        #     print(f"  {i}: {voice.name} ({voice.id})")

    def _speak_text(self, str):
        try:
            self.tts_engine.say(str)
        except Exception as e:
            print(f"TTS Error: {e}")
    
    def voiceToneOutputToFile(self, prompt: str, tone: str = "neutral", filename: str = "output.wav") -> str:
        """Generate text and save as audio file with specified tone"""
        text_response = self.chat(prompt)
    
        # Configure voice
        profile = self.voice_profiles.get(tone.lower(), self.voice_profiles["neutral"])
        self._configure_voice(profile)
    
        # Save to file
        self.tts_engine.save_to_file(text_response, filename)
        self.tts_engine.runAndWait()
    
        return text_response
    


    def workoutPlanChatBot(self, inputs: Dict[str, Any]) -> str:
        #Create a workout unique workout plan for user using gemini

        #Validate required inputs
        required_fields = ['goal', 'fitness_level', 'available_time_per_session', 'days_per_week']
        missing_fields = [field for field in required_fields if not inputs.get(field)]

        if missing_fields:
            return f"Missing required information: {', '.join(missing_fields)}. Please provide these details for a proper workout plan. "

        prompt = (f"""
        You are a certified fitness trainer AI with expertise in exercise science and program design.
        Create a comprehensive, personalized workout plan based on the following profile:

        PERSONAL PROFILE:
        Name: {inputs.get('name', 'User')}
        Gender: {inputs.get('gender')}
        Height: {inputs.get('height')}
        Weight: {inputs.get('weight')}
        Primary Goal: {inputs.get('goal')}
        Current Fitness Level: {inputs.get('fitness_level')}
        Available Equipment: {inputs.get('available_equipment', 'Bodyweight only')}
        Time Per Session: {inputs.get('available_time_per_session')} minutes
        Training Days Per Week: {inputs.get('days_per_week')}
        Target Muscle Groups: {inputs.get('target_muscle_groups', 'Full body')}
        Any Limitations/Injuries: {inputs.get('limitations', 'None specified')}
        Experience Level: {inputs.get('experience_level', 'Beginner')}

        WORKOUT PLAN STRUCTURE:
        1. **Program Overview** (2-3 sentences about the approach)
        
        2. **Weekly Schedule** 
           - Day-by-day breakdown with specific focus areas
           - Rest day recommendations
        
        3. **Detailed Daily Workouts**
           For each training day include:
           - Warm-up routine (5-10 minutes)
           - Main exercises with sets × reps or duration
           - Rest periods between sets
           - Exercise modifications for different levels
           - Cool-down routine (5-10 minutes)
        
        4. **Progressive Overload Guidelines**
           - How to increase difficulty over time
           - When to progress (weekly/biweekly)
        
        5. **Form Cues & Safety Tips**
           - Key technique points for main exercises
           - Common mistakes to avoid
        
        6. **Motivational Closing**
           - Encouraging message
           - Expected timeline for results
           - Reminder about consistency

        Make the plan specific, actionable, and appropriate for their fitness level.
        """
                  )
        

        return self.chat(prompt)


    from typing import List

    def formCorrectionFeedback(self, score: int, feedback_list: List[str], exercise_name: str = "an exercise") -> str:
        """
        Generates AI feedback based on CV pose analysis.

        Args:
            score (int): Pose quality score from 0–100
            feedback_list (List[str]): Observations from pose analysis
            exercise_name (str): Name of the exercise, e.g. "push-up", "squat"

        Returns:
            str: Natural-language form feedback from Gemini
        """

        tone = "encouraging" if score >= 70 else "constructive and supportive"

        prompt = (
            f"You are a {tone} virtual fitness coach helping a user improve their form.\n"
            f"They are performing a {exercise_name}.\n\n"
            f"The computer vision system gave them a score of {score}/100.\n"
            f"Here are the posture observations:\n"
            + "\n".join(f"- {item}" for item in feedback_list) +
            "\n\nGive personalized feedback to help them improve their form. Be specific, clear, and motivational."
        )

        return self.chat(prompt)