import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 65)
print("     🔍 AUTOMATED COMPOSIO AIRTABLE BASE DISCOVERY 🔍")
print("=" * 65)

try:
    from composio import Composio
    from composio_langgraph import LanggraphProvider

    composio = Composio(provider=LanggraphProvider())
    session = composio.create(user_id="presenceix_lead_session")
    
    print("🔌 Connecting to your connected Airtable account via Composio...")
    
    # List of common base listing actions
    base_actions = ["airtable_list_bases", "airtable_get_bases", "airtable_list_all_bases"]
    
    success = False
    for action in base_actions:
        try:
            print(f"📡 Executing action: '{action}'...")
            result = session.execute(tool_slug=action, arguments={})
            
            if hasattr(result, "model_dump"):
                res_dict = result.model_dump()
            elif hasattr(result, "dict"):
                res_dict = result.dict()
            elif isinstance(result, dict):
                res_dict = result
            else:
                res_dict = {"raw": str(result)}
                
            # Print discovered bases
            data = res_dict.get("data", {})
            bases = data.get("bases", []) or res_dict.get("bases", [])
            
            if bases:
                print("\n🎉 DISCOVERED AIRTABLE BASES IN YOUR ACCOUNT:")
                print("-" * 65)
                for b in bases:
                    name = b.get("name", "Unknown Name")
                    base_id = b.get("id", "Unknown ID")
                    print(f"  ⭐ Base Name: {name:<25} | Base ID: {base_id}")
                    if "presenceix" in name.lower():
                        print(f"  👉 (Recommended Base ID to use: '{base_id}')")
                print("-" * 65)
                success = True
                break
        except Exception as e:
            # Try next action if this fails
            continue
            
    if not success:
        print("\n⚠️ Note: Could not auto-list bases because the account is brand new or list action returned empty.")
        print("Please check your browser URL bar for the Base ID (starts with 'app...').")
        
except Exception as e:
    print(f"❌ Error during Discovery execution: {e}")
    
print("\n" + "=" * 65)
