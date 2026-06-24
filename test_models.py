import os
import sys
from dotenv import load_dotenv

# Load configurations
load_dotenv()

print("=" * 65)
print("         🧪 PRESENCEIX MULTI-MODEL ROUTER TESTER 🧪")
print("=" * 65)

# Verify if we can import the router
try:
    from llm_router import get_llm
except ImportError as e:
    print(f"❌ Error importing llm_router: {e}")
    sys.exit(1)

# List of all available providers
providers = {
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY"
}

# Print status of API keys
print("\n🔑 Configured API Keys Status:")
for provider, env_var in providers.items():
    key_val = os.getenv(env_var)
    if not key_val or "your_" in key_val:
        status = "🔴 Missing / Placeholder"
    else:
        status = f"🟢 Present ({key_val[:8]}...)"
    print(f"  - {provider.upper():<10} ({env_var}): {status}")

print("\n" + "-" * 65)

# Read active provider and model
active_provider = os.getenv("LLM_PROVIDER", "openai").lower()
active_model = os.getenv("LLM_MODEL", "default")

print(f"🎯 ACTIVE ROUTER SETTINGS:")
print(f"  - LLM_PROVIDER: {active_provider.upper()}")
print(f"  - LLM_MODEL   : {active_model.upper()}")
print("-" * 65)

# Attempt to load the active LLM
print("\n🤖 Initializing Active LLM...")
try:
    llm = get_llm(temperature=0.3)
    print("🟢 LLM initialized successfully!")
    
    # Test prompt
    prompt = "Hello! Tell me in 1 sentence who you are and which model you are running on."
    print(f"\n💬 Sending Test Prompt: '{prompt}'")
    print("⏳ Invoking...")
    
    response = llm.invoke(prompt)
    print("\n📝 Response:")
    print("=" * 65)
    print(response.content.strip())
    print("=" * 65)
    
except Exception as e:
    print(f"\n❌ Error initializing or invoking model: {e}")
    print("\n💡 Tip: If you tried a new provider (like Groq or DeepSeek) and don't have a key,")
    print("   the router will automatically try to fall back to OpenAI as a safety net!")

print("\n" + "=" * 65)
