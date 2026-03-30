"""
AI Chatbot Service
Powered by Google Gemini 1.5 Flash.
Acts as an expert ESG financial advisor.
"""
import google.generativeai as genai

class ChatbotService:
    def __init__(self):
        # 🛑 PASTE YOUR GEMINI API KEY HERE
        self.api_key = "YOUR_GEMINI_API_KEY"
        
        if self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def get_response(self, user_message):
        if not self.model:
            return "⚠️ Please add your Gemini API Key in `backend/services/chatbot_service.py` to activate me!"

        # We give the AI a "System Persona" so it knows how to act
        prompt = f"""You are ESGVision AI, a highly intelligent and helpful financial advisor specializing in ESG (Environmental, Social, and Governance) investing and the stock market. 
Keep your answers concise, professional, and easy to read. Do not use markdown headers, just plain text and bullet points if necessary.

User Question: {user_message}"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Chatbot Error: {e}")
            return "I'm sorry, I encountered an error connecting to the AI brain. Please try again later."