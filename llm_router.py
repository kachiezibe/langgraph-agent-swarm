import os
from dotenv import load_dotenv

# Ensure keys are loaded
load_dotenv()

def get_llm(temperature=0.5, streaming=False):
    """
    PresenceIX Unified LLM Router.
    Reads config from .env to load any supported AI model automatically.
    
    Supported providers:
      - openai     -> OpenAI GPT models (Default: gpt-4o-mini)
      - groq       -> Groq Llama/Mixtral (Default: llama-3.1-8b-instant)
      - deepseek   -> DeepSeek Chat/Coder (Default: deepseek-chat)
      - mistral    -> Mistral AI (Default: open-mistral-7b)
      - gemini     -> Google Gemini (Default: gemini-1.5-flash)
      - anthropic  -> Anthropic Claude (Default: claude-3-haiku-20240307)
      - openrouter -> OpenRouter (Default: meta-llama/llama-3.1-8b-instruct:free)
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()
    model = os.getenv("LLM_MODEL", "").strip()

    # Fallback to OpenAI if provider is unrecognized
    if provider not in ["openai", "groq", "deepseek", "mistral", "gemini", "anthropic", "openrouter"]:
        print(f"⚠️  [Router] Warning: Unknown provider '{provider}'. Defaulting to 'openai'.")
        provider = "openai"

    print(f"🔌 [Router] Connecting to provider: '{provider.upper()}' ...")

    # ==========================================
    # 1. OPENAI (GPT-4o / GPT-4o-mini)
    # ==========================================
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or "your_openai_api_key_here" in api_key:
            raise ValueError("❌ [Router] Error: OpenAI API Key is missing or misconfigured in .env")
        
        target_model = model if model else "gpt-4o-mini"
        print(f"🧠 [Router] Brain Selected: OpenAI '{target_model}'")
        return ChatOpenAI(
            model=target_model,
            temperature=temperature,
            streaming=streaming,
            api_key=api_key
        )

    # ==========================================
    # 2. GROQ (Llama / Mixtral)
    # ==========================================
    elif provider == "groq":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or "your_groq_api_key_here" in api_key:
            print("⚠️  [Router] Warning: Groq key not configured. Falling back to OpenAI (gpt-4o-mini).")
            # Clear provider to run fallback config safely
            os.environ["LLM_PROVIDER"] = "openai"
            os.environ["LLM_MODEL"] = "gpt-4o-mini"
            return get_llm(temperature=temperature, streaming=streaming)
            
        target_model = model if model else "llama-3.1-8b-instant"
        print(f"🧠 [Router] Brain Selected: Groq '{target_model}' (OpenAI Adapter)")
        return ChatOpenAI(
            model=target_model,
            temperature=temperature,
            streaming=streaming,
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    # ==========================================
    # 3. DEEPSEEK (Chat / Coder)
    # ==========================================
    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or "your_deepseek_api_key_here" in api_key:
            print("⚠️  [Router] Warning: DeepSeek key not configured. Falling back to OpenAI (gpt-4o-mini).")
            os.environ["LLM_PROVIDER"] = "openai"
            os.environ["LLM_MODEL"] = "gpt-4o-mini"
            return get_llm(temperature=temperature, streaming=streaming)
            
        target_model = model if model else "deepseek-chat"
        print(f"🧠 [Router] Brain Selected: DeepSeek '{target_model}' (OpenAI Adapter)")
        return ChatOpenAI(
            model=target_model,
            temperature=temperature,
            streaming=streaming,
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )

    # ==========================================
    # 4. MISTRAL AI
    # ==========================================
    elif provider == "mistral":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key or "your_mistral_api_key_here" in api_key:
            print("⚠️  [Router] Warning: Mistral key not configured. Falling back to OpenAI (gpt-4o-mini).")
            os.environ["LLM_PROVIDER"] = "openai"
            os.environ["LLM_MODEL"] = "gpt-4o-mini"
            return get_llm(temperature=temperature, streaming=streaming)
            
        target_model = model if model else "open-mistral-7b"
        print(f"🧠 [Router] Brain Selected: Mistral '{target_model}' (OpenAI Adapter)")
        return ChatOpenAI(
            model=target_model,
            temperature=temperature,
            streaming=streaming,
            api_key=api_key,
            base_url="https://api.mistral.ai/v1"
        )

    # ==========================================
    # 5. GOOGLE GEMINI
    # ==========================================
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or "your_google_gemini_api_key_here" in api_key:
            print("⚠️  [Router] Warning: Gemini key not configured. Falling back to OpenAI (gpt-4o-mini).")
            os.environ["LLM_PROVIDER"] = "openai"
            os.environ["LLM_MODEL"] = "gpt-4o-mini"
            return get_llm(temperature=temperature, streaming=streaming)
            
        target_model = model if model else "gemini-1.5-flash"
        print(f"🧠 [Router] Brain Selected: Google Gemini '{target_model}'")
        return ChatGoogleGenerativeAI(
            model=target_model,
            temperature=temperature,
            api_key=api_key
        )

    # ==========================================
    # 6. ANTHROPIC CLAUDE
    # ==========================================
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or "your_anthropic_api_key_here" in api_key:
            print("⚠️  [Router] Warning: Anthropic key not configured. Falling back to OpenAI (gpt-4o-mini).")
            os.environ["LLM_PROVIDER"] = "openai"
            os.environ["LLM_MODEL"] = "gpt-4o-mini"
            return get_llm(temperature=temperature, streaming=streaming)
            
        target_model = model if model else "claude-3-haiku-20240307"
        print(f"🧠 [Router] Brain Selected: Anthropic Claude '{target_model}'")
        return ChatAnthropic(
            model=target_model,
            temperature=temperature,
            streaming=streaming,
            api_key=api_key
        )

    # ==========================================
    # 7. OPENROUTER (Llama / Qwen / Mistral / Free models)
    # ==========================================
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or "your_openrouter_api_key_here" in api_key:
            print("⚠️  [Router] Warning: OpenRouter key not configured. Falling back to OpenAI (gpt-4o-mini).")
            os.environ["LLM_PROVIDER"] = "openai"
            os.environ["LLM_MODEL"] = "gpt-4o-mini"
            return get_llm(temperature=temperature, streaming=streaming)
            
        target_model = model if model else "meta-llama/llama-3.1-8b-instruct:free"
        print(f"🧠 [Router] Brain Selected: OpenRouter '{target_model}'")
        return ChatOpenAI(
            model=target_model,
            temperature=temperature,
            streaming=streaming,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://presenceix.com",
                "X-Title": "PresenceIX Swarm",
            }
        )
