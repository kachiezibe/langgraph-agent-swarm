import os
import json
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

print("=" * 65)
print("       🧪 LIVE COMPOSIO TOOL CALL TESTER 🧪")
print("=" * 65)

# Initialize Composio SDK
print("🔌 Initializing Composio with LanggraphProvider...")
try:
    from composio import Composio
    from composio_langgraph import LanggraphProvider

    composio = Composio(provider=LanggraphProvider())
    print("🟢 Success: Composio initialized successfully!")
    
    # Check connected accounts
    print("\n🔍 Querying connected integrations on Composio...")
    accounts = composio.connected_accounts.list()
    active_apps = []
    print(f"🟢 Success: Found {len(accounts.items)} total connected account entries.")
    
    print("\n📋 Connection Status:")
    for acc in accounts.items:
        app_name = acc.toolkit.slug if hasattr(acc.toolkit, "slug") else getattr(acc.toolkit, "name", "unknown")
        status = acc.status
        user = acc.user_id
        print(f"  - App: {app_name:<15} | Status: {status:<10} | User ID: {user}")
        if status == "ACTIVE":
            active_apps.append((app_name, acc))

    print(f"\n🟢 Found {len(active_apps)} ACTIVE connected apps.")

    # Create a session for 'presenceix_lead_session'
    print("\n📂 Initializing tool session for 'presenceix_lead_session'...")
    session = composio.create(user_id="presenceix_lead_session")
    tools = session.tools()
    print(f"🟢 Success: Loaded {len(tools)} total actions/tools in session!")
    
    print("\n📋 All Loaded Session Tools:")
    for idx, tool in enumerate(tools, 1):
        print(f"  {idx}. {tool.name:<35} - {tool.description[:60]}...")

    # Query hunter tools specifically via top-level sdk
    print("\n🔍 Querying Hunter.io tools specifically using composio.tools.get()...")
    hunter_tools = composio.tools.get(user_id="presenceix_lead_session", toolkits=["hunter"])
    print(f"🟢 Success: Loaded {len(hunter_tools)} Hunter.io tools from SDK!")
    if hunter_tools:
        print("\n📋 All Hunter.io Tools:")
        for idx, tool in enumerate(hunter_tools, 1):
            name = getattr(tool, "name", getattr(tool, "slug", str(tool)))
            description = getattr(tool, "description", "")
            print(f"  {idx}. {name:<35} - {description[:60]}...")
            
        # Try a live verification call on Hunter.io!
        target_email = "test@presenceix.com"
        verify_action_obj = next((t for t in hunter_tools if "verify" in getattr(t, "name", "").lower() or "verifier" in getattr(t, "name", "").lower()), hunter_tools[0])
        verify_action = getattr(verify_action_obj, "name", str(verify_action_obj))
        
        print(f"\n⚡ Executing live tool call on Hunter.io: {verify_action} for '{target_email}'...")
        try:
            action_result = session.execute(tool_slug=verify_action, arguments={"email": target_email})
            
            # Convert response to dictionary safely
            if hasattr(action_result, "model_dump"):
                result_dict = action_result.model_dump()
            elif hasattr(action_result, "dict"):
                result_dict = action_result.dict()
            elif isinstance(action_result, dict):
                result_dict = action_result
            else:
                result_dict = {"raw": str(action_result)}
                
            print("\n🎉 LIVE TOOL CALL EXECUTED SUCCESSFULLY!")
            print("📝 Response Data:")
            print("-" * 65)
            print(json.dumps(result_dict, indent=2))
            print("-" * 65)
        except Exception as exec_err:
            print(f"❌ Live tool call execution failed: {exec_err}")
    else:
        print("⚠️ No Hunter.io tools returned in the session. Make sure the 'hunter' app is enabled in dashboard.")

except Exception as init_err:
    print(f"❌ Initialization or lookup failed: {init_err}")

print("\n" + "=" * 65)
