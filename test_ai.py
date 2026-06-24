import os
from dotenv import load_dotenv

# 1. Load keys from .env file
load_dotenv()

# Get the keys
gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

print("=" * 50)
print("        🧪 TESTING YOUR AI KEYS 🧪")
print("=" * 50)

# Test Gemini
if gemini_key and gemini_key != "your_google_gemini_api_key_here":
    print("🤖 Testing Google Gemini...")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")
        response = llm.invoke("Say 'Google Gemini setup is 100% successful!' and give me a 1-sentence tip on building AI agents.")
        print(f"🟢 Gemini Success:\n{response.content}\n")
    except Exception as e:
        print(f"❌ Gemini Failed: {e}\n")
else:
    print("⚪ Gemini: No key configured.\n")

print("-" * 50)

# Test OpenAI
if openai_key and openai_key != "your_openai_api_key_here":
    print("🤖 Testing OpenAI GPT...")
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini")
        response = llm.invoke("Say 'OpenAI GPT setup is 100% successful!' and give me a 1-sentence tip on building AI agents.")
        print(f"🟢 OpenAI Success:\n{response.content}\n")
    except Exception as e:
        print(f"❌ OpenAI Failed: {e}\n")
else:
    print("⚪ OpenAI: No key configured.\n")

print("=" * 50)
