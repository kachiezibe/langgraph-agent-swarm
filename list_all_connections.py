import os
from dotenv import load_dotenv

load_dotenv()

try:
    from composio import Composio
    from composio_langgraph import LanggraphProvider

    composio = Composio(provider=LanggraphProvider())
    print("🔌 Querying all connections in your Composio workspace...")
    accounts = composio.connected_accounts.list()
    
    print("\n📋 FOUND CONNECTIONS:")
    print("=" * 75)
    print(f"{'App Slug':<18} | {'Status':<12} | {'Connection ID':<20} | {'User/Entity ID'}")
    print("-" * 75)
    
    for acc in accounts.items:
        app_name = acc.toolkit.slug if hasattr(acc.toolkit, "slug") else getattr(acc.toolkit, "name", "unknown")
        status = acc.status
        conn_id = acc.id
        user = acc.user_id
        print(f"{app_name:<18} | {status:<12} | {conn_id:<20} | {user}")
    print("=" * 75)

except Exception as e:
    print(f"❌ Error listing connections: {e}")
