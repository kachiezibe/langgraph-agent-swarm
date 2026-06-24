import os
import sys
from dotenv import load_dotenv

# Load configurations from .env
load_dotenv()

print("=" * 65)
print("          🧪 PRESENCEIX COMPOSIO CONNECTOR TESTER 🧪")
print("=" * 65)

# Verify if we can import the new modern Composio SDK and LanggraphProvider
print("📦 Verifying modern Composio libraries...")
try:
    from composio import Composio
    from composio_langgraph import LanggraphProvider
    print("🟢 Success: Modern Composio SDK & LanggraphProvider are installed and loadable!")
except ImportError as e:
    print(f"❌ Error: Modern Composio package is not loadable. details: {e}")
    print("\n💡 Tip: Make sure you have installed 'composio_langgraph' inside the virtual environment.")
    sys.exit(1)

# Initialize Composio Client
print("\n🔌 Initializing Composio Client...")
try:
    # This automatically picks up COMPOSIO_API_KEY from the environment
    composio = Composio(provider=LanggraphProvider())
    print("🟢 Success: Composio Client initialized successfully!")
    
    # Create a user session for testing local tools
    print("\n📂 Initializing test session and loading tools...")
    session = composio.create(user_id="test_user_presenceix")
    
    # Get tools (e.g. File Tool which requires no complex OAuth)
    tools = session.tools()
    
    print(f"\n🟢 Success: Loaded {len(tools)} tools from Composio successfully!")
    print("📋 Available Session Actions:")
    for idx, tool in enumerate(tools[:5], 1):
        print(f"  {idx}. {tool.name:<25} - {tool.description[:60]}...")
    if len(tools) > 5:
        print(f"  ... and {len(tools) - 5} more tools.")
        
    print("\n🎉 Connection plumbing is fully functional! You are ready to connect Google, Airtable, etc.")
    
except Exception as e:
    print(f"\n❌ Error during Composio initialization: {e}")
    print("\n💡 Troubleshooting Steps:")
    print("  1. Go to your Composio Dashboard: https://dashboard.composio.dev")
    print("  2. Click on 'Settings' (the gear icon on the bottom left sidebar).")
    print("  3. Copy your master 'Developer API Key'.")
    print("  4. Paste it into your .env file as: COMPOSIO_API_KEY=\"your_key\"")

print("\n" + "=" * 65)
