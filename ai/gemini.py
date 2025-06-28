import os
import google.generativeai as genai
from .base import AIPlatform


class Gemini(AIPlatform):
    def init(self, api_key: str, system_prompt: str = None):
        self.api_key = api_key
        self.system_prompt = system_prompt
        genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

    def chat(self, prompt: str) -> str:
        if self.system_prompt:
            prompt = f"{self.system_prompt}\n\n{prompt}"

        response = self.model.generate_content(prompt)
        return response.text
    def voiceToneOutput(self, input):
        #textToSpeech
        #Gemini (text generation) → Google TTS (audio)

    def workoutPlanChatBot(self, inputs):
        #code the AI chatbot
        #Gemini (text-based prompts)
    def formCorrectionFeedback(self, input):
        #Gemini (pose summary → feedback text)
    def realTimeChatbot(self, input):