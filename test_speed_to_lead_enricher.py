import os
import json
from dotenv import load_dotenv

# Load .env configurations
load_dotenv()

print("=" * 65)
print("     🧪 TESTING SPEED-TO-LEAD LIVE ENRICHER NODE 🧪")
print("=" * 65)

# Import the enricher node function
try:
    from agent_speed_to_lead import enrich_lead_node
    print("🟢 Success: Imported enrich_lead_node from agent_speed_to_lead.py")
except ImportError as e:
    print(f"❌ Error: Could not import enrich_lead_node. Details: {e}")
    exit(1)

# Set up test state
test_state = {
    "lead_id": "test_lead_12345",
    "name": "Jane Doe",
    "phone": "+1-555-9876",
    "email": "test@presenceix.com",
    "source": "Zillow Portal Test",
    "enriched_info": "",
    "dialog_history": [],
    "scores": {},
    "final_score": 0.0,
    "status": "IN_PROGRESS",
    "logs": []
}

print("\n🚀 Executing enrich_lead_node...")
try:
    result_state = enrich_lead_node(test_state)
    print("\n🟢 Success: enrich_lead_node completed successfully!")
    print("\n📝 Resulting Enriched Info:")
    print("-" * 65)
    print(result_state.get("enriched_info"))
    print("-" * 65)
    print("\n📝 Execution Logs:")
    for log in result_state.get("logs", []):
        print(f"  - {log}")
except Exception as e:
    print(f"❌ Error executing enrich_lead_node: {e}")

print("\n" + "=" * 65)
