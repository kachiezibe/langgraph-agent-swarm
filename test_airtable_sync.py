from dotenv import load_dotenv
from airtable_sync import sync_lead_to_airtable, sync_content_to_airtable, is_airtable_configured_rest, is_airtable_connected_in_composio

load_dotenv()


print("=" * 65)
print("       🧪 TESTING AIRTABLE INTEGRATION SYNCHRONIZATION 🧪")
print("=" * 65)

print(f"📡 Composio Active Connection : {is_airtable_connected_in_composio()}")
print(f"📡 REST Direct Fallback Active : {is_airtable_configured_rest()}")


# Mock lead record
mock_lead = {
    "lead_id": "test_sync_lead_999",
    "name": "Alex Mercer",
    "phone": "+1-555-0999",
    "email": "alex.mercer@gmail.com",
    "source": "Zillow Portal",
    "enriched_info": "Interested in 4-bed suburban home with spacious yard, $750k budget.",
    "dialog_history": [
        {"role": "agent", "content": "Hi Alex! Are you looking to move soon or just browsing?"},
        {"role": "user", "content": "Looking to move in the next 30 days, relocating from SF."}
    ],
    "scores": {"budget": 8.0, "timeline": 9.0, "motivation": 8.5, "representation": 10.0},
    "final_score": 8.8,
    "status": "QUALIFIED"
}

# Mock content draft
mock_content = {
    "topic": "Why autonomous AI agents are the future of lead response in real estate.",
    "linkedin_draft": "🚨 Real estate brokers: If your lead response takes >5 minutes, you've already lost the client...",
    "x_thread": "1/ Why your real estate CRM is leaking money (and how AI swarms fix it) 🧵",
    "video_script": "[VISUAL: Agent looking at screen] VOICE: This AI concierge handles leads 24/7...",
    "status": "DRAFT"
}

print("\n🚀 1. Simulating Lead Sync...")
lead_result = sync_lead_to_airtable(mock_lead)
print(f"📊 Result: {'🟢 SUCCESS' if lead_result else '🟡 SKIPPED / FAILED (Graceful Fallback)'}")

print("\n🚀 2. Simulating Content Calendar Sync...")
content_result = sync_content_to_airtable(mock_content)
print(f"📊 Result: {'🟢 SUCCESS' if content_result else '🟡 SKIPPED / FAILED (Graceful Fallback)'}")

print("\n" + "=" * 65)
print("🎉 Airtable sync test run completed!")
print("=" * 65)
