import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load credentials
load_dotenv()

# Configuration variables
AIRTABLE_PAT = os.getenv("AIRTABLE_PERSONAL_ACCESS_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_LEADS_TABLE = os.getenv("AIRTABLE_LEADS_TABLE", "Leads")
AIRTABLE_CONTENT_TABLE = os.getenv("AIRTABLE_CONTENT_TABLE", "Content Calendar")

def _print_guide_box():
    print("\n" + "═" * 70)
    print(" 🔌  COMPOSIO / AIRTABLE CONNECTION GUIDE  🔌")
    print("═" * 70)
    print(" You have selected to run Airtable directly via Composio (SaaS Mode)!")
    print(" To authorize Airtable inside your PresenceIX Composio workspace, run:")
    print("\n   venv/bin/composio add airtable --user-id presenceix_lead_session\n")
    print(" This will open a secure OAuth pop-up in your browser. Just authorize")
    print(" your Airtable base and everything will sync automatically in 1-click.")
    print("\n 📝 Alternatively, you can add standard credentials to your '.env':")
    print("    AIRTABLE_PERSONAL_ACCESS_TOKEN=\"pat_your_token_here\"")
    print("    AIRTABLE_BASE_ID=\"app_your_base_id_here\"")
    print("═" * 70)
    print(" 👉 Saving lead/content payload locally in 'outputs/' instead...\n")


def is_airtable_connected_in_composio() -> bool:
    """Checks if Airtable is actively connected in your Composio workspace."""
    try:
        from composio import Composio
        from composio_langgraph import LanggraphProvider
        composio = Composio(provider=LanggraphProvider())
        accounts = composio.connected_accounts.list()
        for acc in accounts.items:
            app_name = acc.toolkit.slug if hasattr(acc.toolkit, "slug") else getattr(acc.toolkit, "name", "unknown")
            if "airtable" in app_name.lower() and acc.status == "ACTIVE":
                return True
        return False
    except Exception:
        return False


def is_airtable_configured_rest() -> bool:
    """Check if standard Airtable REST credentials are set up."""
    return bool(AIRTABLE_PAT and AIRTABLE_BASE_ID and "your_" not in AIRTABLE_PAT and "your_" not in AIRTABLE_BASE_ID)


def is_airtable_configured() -> bool:
    """Checks if Airtable is configured either via REST or Composio."""
    return is_airtable_configured_rest() or is_airtable_connected_in_composio()


def format_dialog_history(history: list) -> str:
    """Convert JSON dialog history into a clean human-readable chat log."""
    if not history:
        return "No chat history logged."
    
    formatted = []
    for msg in history:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        if role == "Agent":
            role = "PresenceIX AI Agent"
        elif role == "User":
            role = "Prospective Buyer"
        formatted.append(f"[{role}]:\n{content}\n")
    
    return "\n".join(formatted)


def _parse_action_result(action_result) -> dict:
    """Safely parses a Composio tool action execution result into a dictionary."""
    if hasattr(action_result, "model_dump"):
        return action_result.model_dump()
    elif hasattr(action_result, "dict"):
        return action_result.dict()
    elif isinstance(action_result, dict):
        return action_result
    return {}


def _sync_lead_via_composio(lead_data: dict, base_id: str, table_name: str) -> bool:
    """Synchronizes lead record to Airtable using Composio Action Execution."""
    try:
        from composio import Composio
        from composio_langgraph import LanggraphProvider
        
        composio = Composio(provider=LanggraphProvider())
        session = composio.create(user_id="presenceix_lead_session")
        
        lead_id = lead_data.get("lead_id")
        dialog_logs_text = format_dialog_history(lead_data.get("dialog_history", []))
        
        fields = {
            "Lead ID": lead_id,
            "Name": lead_data.get("name", ""),
            "Phone": lead_data.get("phone", ""),
            "Email": lead_data.get("email", ""),
            "Source": lead_data.get("source", "Direct"),
            "Final Score": float(lead_data.get("final_score", 1.0)),
            "Status": lead_data.get("status", "IN_PROGRESS"),
            "Enriched Info": lead_data.get("enriched_info", ""),
            "Dialog Logs": dialog_logs_text
        }
        
        print(f"🔌 [Composio -> Airtable Sync] Querying base for existing lead: '{lead_id}'...")
        
        # 1. Search for existing record
        records = []
        try:
            search_res = session.execute(
                tool_slug="airtable_list_records",
                arguments={
                    "baseId": base_id,
                    "tableIdOrName": table_name,
                    "filterByFormula": f"{{Lead ID}} = '{lead_id}'"
                }
            )
            res_dict = _parse_action_result(search_res)
            # Standard output extraction for list records
            records = res_dict.get("data", {}).get("records", []) or res_dict.get("records", []) or []
        except Exception as search_err:
            print(f"⚠️ [Composio -> Airtable Sync] Search action failed: {search_err}. Assuming new record.")
            records = []

        if records:
            record_id = records[0]["id"]
            print(f"🔄 [Composio -> Airtable Sync] Record found (ID: {record_id}). Performing UPDATE...")
            try:
                session.execute(
                    tool_slug="airtable_update_record",
                    arguments={
                        "baseId": base_id,
                        "tableIdOrName": table_name,
                        "recordId": record_id,
                        "fields": fields
                    }
                )
                print(f"🟢 [Composio -> Airtable Sync] Lead '{lead_id}' updated successfully!")
                return True
            except Exception as upd_err:
                print(f"⚠️ [Composio -> Airtable Sync] update_record action not supported. Trying multi-update fallback...")
                session.execute(
                    tool_slug="airtable_update_records",
                    arguments={
                        "baseId": base_id,
                        "tableIdOrName": table_name,
                        "records": [{"id": record_id, "fields": fields}]
                    }
                )
                print(f"🟢 [Composio -> Airtable Sync] Lead '{lead_id}' updated via fallback!")
                return True
        else:
            print(f"➕ [Composio -> Airtable Sync] Record not found. Performing CREATE...")
            try:
                session.execute(
                    tool_slug="airtable_create_record",
                    arguments={
                        "baseId": base_id,
                        "tableIdOrName": table_name,
                        "fields": fields
                    }
                )
                print(f"🟢 [Composio -> Airtable Sync] Lead '{lead_id}' created successfully!")
                return True
            except Exception as create_err:
                print(f"⚠️ [Composio -> Airtable Sync] create_record action not supported. Trying multi-create fallback...")
                session.execute(
                    tool_slug="airtable_create_records",
                    arguments={
                        "baseId": base_id,
                        "tableIdOrName": table_name,
                        "records": [{"fields": fields}]
                    }
                )
                print(f"🟢 [Composio -> Airtable Sync] Lead '{lead_id}' created via fallback!")
                return True
                
    except Exception as e:
        print(f"❌ [Composio -> Airtable Sync] Synchronization failed: {e}")
        return False


def _sync_content_via_composio(content_data: dict, base_id: str, table_name: str) -> bool:
    """Synchronizes content calendar item to Airtable using Composio Action Execution."""
    try:
        from composio import Composio
        from composio_langgraph import LanggraphProvider
        
        composio = Composio(provider=LanggraphProvider())
        session = composio.create(user_id="presenceix_lead_session")
        
        today_date = datetime.now().strftime("%Y-%m-%d")
        fields = {
            "Topic": content_data.get("topic", ""),
            "Date": today_date,
            "LinkedIn Draft": content_data.get("linkedin_draft", ""),
            "X Thread": content_data.get("x_thread", ""),
            "Video Script": content_data.get("video_script", ""),
            "Status": content_data.get("status", "DRAFT")
        }
        
        print(f"🔌 [Composio -> Airtable Sync] Connecting to add content calendar draft for: '{fields['Topic'][:40]}...'")
        
        try:
            session.execute(
                tool_slug="airtable_create_record",
                arguments={
                    "baseId": base_id,
                    "tableIdOrName": table_name,
                    "fields": fields
                }
            )
            print("🟢 [Composio -> Airtable Sync] Content added to calendar successfully!")
            return True
        except Exception as create_err:
            print(f"⚠️ [Composio -> Airtable Sync] create_record failed: {create_err}. Trying multi-create fallback...")
            session.execute(
                tool_slug="airtable_create_records",
                arguments={
                    "baseId": base_id,
                    "tableIdOrName": table_name,
                    "records": [{"fields": fields}]
                }
            )
            print("🟢 [Composio -> Airtable Sync] Content added to calendar via fallback!")
            return True
            
    except Exception as e:
        print(f"❌ [Composio -> Airtable Sync] Content sync failed: {e}")
        return False


def _sync_lead_via_rest(lead_data: dict, base_id: str, table_name: str) -> bool:
    """Syncs lead record directly using HTTP REST requests with Personal Access Token."""
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    base_url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    lead_id = lead_data.get("lead_id")
    dialog_logs_text = format_dialog_history(lead_data.get("dialog_history", []))
    
    fields = {
        "Lead ID": lead_id,
        "Name": lead_data.get("name", ""),
        "Phone": lead_data.get("phone", ""),
        "Email": lead_data.get("email", ""),
        "Source": lead_data.get("source", "Direct"),
        "Final Score": float(lead_data.get("final_score", 1.0)),
        "Status": lead_data.get("status", "IN_PROGRESS"),
        "Enriched Info": lead_data.get("enriched_info", ""),
        "Dialog Logs": dialog_logs_text
    }
    
    print(f"🔌 [REST -> Airtable Sync] Querying base for existing lead: '{lead_id}'...")
    params = {"filterByFormula": f"{{Lead ID}} = '{lead_id}'"}
    
    try:
        search_response = requests.get(base_url, headers=headers, params=params)
        if search_response.status_code != 200:
            print(f"❌ [REST -> Airtable Sync] Search failed (HTTP {search_response.status_code})")
            return False
            
        search_data = search_response.json()
        records = search_data.get("records", [])
        
        if records:
            record_id = records[0]["id"]
            print(f"🔄 [REST -> Airtable Sync] Record found (ID: {record_id}). Performing UPDATE...")
            update_url = f"{base_url}/{record_id}"
            update_response = requests.patch(update_url, headers=headers, json={"fields": fields})
            if update_response.status_code == 200:
                print("🟢 [REST -> Airtable Sync] Lead updated successfully!")
                return True
        else:
            print("➕ [REST -> Airtable Sync] Record not found. Performing CREATE...")
            create_response = requests.post(base_url, headers=headers, json={"fields": fields})
            if create_response.status_code in [200, 201]:
                print("🟢 [REST -> Airtable Sync] Lead created successfully!")
                return True
        return False
    except Exception as e:
        print(f"❌ [REST -> Airtable Sync] Sync exception: {e}")
        return False


def _sync_content_via_rest(content_data: dict, base_id: str, table_name: str) -> bool:
    """Syncs content draft directly using HTTP REST requests with Personal Access Token."""
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    base_url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    fields = {
        "Topic": content_data.get("topic", ""),
        "Date": today_date,
        "LinkedIn Draft": content_data.get("linkedin_draft", ""),
        "X Thread": content_data.get("x_thread", ""),
        "Video Script": content_data.get("video_script", ""),
        "Status": content_data.get("status", "DRAFT")
    }
    
    print(f"🔌 [REST -> Airtable Sync] Adding content calendar draft for: '{fields['Topic'][:40]}...'")
    try:
        create_response = requests.post(base_url, headers=headers, json={"fields": fields})
        if create_response.status_code in [200, 201]:
            print("🟢 [REST -> Airtable Sync] Content added to calendar successfully!")
            return True
        return False
    except Exception as e:
        print(f"❌ [REST -> Airtable Sync] Content sync exception: {e}")
        return False


# ==========================================
# PUBLIC INTERFACE FUNCTIONS
# ==========================================

def sync_lead_to_airtable(lead_data: dict) -> bool:
    """
    Synchronizes a lead record to Airtable CRM.
    Automatically detects and executes via Composio (SaaS Mode) if active, 
    otherwise falls back to Direct REST API or Local JSON files.
    """
    base_id = os.getenv("AIRTABLE_BASE_ID")
    if not base_id or "your_" in base_id:
        # Check if we can search or use a default base ID or fall back
        print("⚠️ [Airtable Sync] AIRTABLE_BASE_ID is not set in '.env'. Cannot sync to cloud.")
        _print_guide_box()
        return False

    table_name = AIRTABLE_LEADS_TABLE

    # 1. Try Composio Mode
    if is_airtable_connected_in_composio():
        print("⚡ [Airtable Sync] Composio connection detected! Routing sync via COMPOSIO Actions...")
        return _sync_lead_via_composio(lead_data, base_id, table_name)

    # 2. Try Direct REST Fallback
    if is_airtable_configured_rest():
        print("⚡ [Airtable Sync] Direct REST credentials found. Routing sync via DIRECT REST Requests...")
        return _sync_lead_via_rest(lead_data, base_id, table_name)

    # 3. Skip/Fallback Guide
    _print_guide_box()
    return False


def sync_content_to_airtable(content_data: dict) -> bool:
    """
    Synchronizes a content calendar post draft to Airtable Content Calendar.
    Automatically detects and executes via Composio (SaaS Mode) if active,
    otherwise falls back to Direct REST API or Local JSON files.
    """
    base_id = os.getenv("AIRTABLE_BASE_ID")
    if not base_id or "your_" in base_id:
        print("⚠️ [Airtable Sync] AIRTABLE_BASE_ID is not set in '.env'. Cannot sync to cloud.")
        _print_guide_box()
        return False

    table_name = AIRTABLE_CONTENT_TABLE

    # 1. Try Composio Mode
    if is_airtable_connected_in_composio():
        print("⚡ [Airtable Sync] Composio connection detected! Routing sync via COMPOSIO Actions...")
        return _sync_content_via_composio(content_data, base_id, table_name)

    # 2. Try Direct REST Fallback
    if is_airtable_configured_rest():
        print("⚡ [Airtable Sync] Direct REST credentials found. Routing sync via DIRECT REST Requests...")
        return _sync_content_via_rest(content_data, base_id, table_name)

    # 3. Skip/Fallback Guide
    _print_guide_box()
    return False
