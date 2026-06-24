import os
import sys
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

# Load configurations
load_dotenv()

# Import the independent agent swarms
try:
    from agent_content_brain import get_content_brain_graph
    from agent_speed_to_lead import process_incoming_message, get_speed_to_lead_graph
except ImportError as e:
    print(f"❌ [Error] Failed to import agent modules: {e}")
    sys.exit(1)


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    print("=" * 65)
    print("         🚀 PRESENCEIX AUTONOMOUS SWARM ORCHESTRATOR 🚀")
    print("=" * 65)
    print(f"  System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Status     : All Swarms Active & Persisted")
    print("  Database   : SQLite Engaged (presenceix_memory.sqlite)")
    print("  Tracing    : LangSmith Active")
    print("=" * 65)


def run_content_brain():
    clear_console()
    print("=" * 65)
    print("       🧠 SWARM A: THE CONTENT BRAIN (7-DAY PLANNER) 🧠")
    print("=" * 65)
    
    topic = input("\n📝 Enter the core topic or trend for this week's content:\n👉 ")
    if not topic.strip():
        print("❌ Error: Topic cannot be empty!")
        input("\nPress Enter to return to main menu...")
        return

    print("\n⏳ Initializing Content Brain Parallel Swarm (SQLite Session)...")
    print("  - Launching Researcher Node (Trend Discovery)...")
    print("  - Forking Parallel Writers (LinkedIn, X, Video Scripts)...")
    print("  - Engaging Exporter Node...")
    print("-" * 65)

    initial_state = {
        "topic": topic,
        "research_notes": "",
        "linkedin_draft": "",
        "x_thread": "",
        "video_script": "",
        "logs": []
    }

    # Generate a unique thread ID for the SQLite save state
    session_id = f"content_session_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}

    from langgraph.checkpoint.sqlite import SqliteSaver
    try:
        with SqliteSaver.from_conn_string("presenceix_memory.sqlite") as memory:
            app = get_content_brain_graph(checkpointer=memory)
            final_output = app.invoke(initial_state, config=config)
            
        print("\n" + "=" * 65)
        print("🎉 CONTENT CALENDAR GENERATION COMPLETE!")
        print("=" * 65)
        print(f"\n📢 TOPIC: {final_output['topic']}")
        
        print("\n--- 💼 LINKEDIN DRAFT ---")
        print(final_output.get("linkedin_draft", "No draft created."))
        
        print("\n--- 🐦 X THREAD DRAFT ---")
        print(final_output.get("x_thread", "No draft created."))
        
        print("\n--- 🎬 VIDEO SCRIPT ---")
        print(final_output.get("video_script", "No draft created."))
        
        print("\n" + "=" * 65)
        print("💾 OUTPUT EXPORTS:")
        # Look in outputs/ directory
        import glob
        files = sorted(glob.glob("outputs/content_draft_*.json"), key=os.path.getmtime)
        if files:
            print(f"  🟢 Local JSON Draft Saved: {files[-1]}")
        print("  🟢 Queue Payload prepared for Notion & Airtable scheduling.")
        print("=" * 65)
        
    except Exception as e:
        print(f"❌ Swarm Execution Error: {e}")

    input("\nPress Enter to return to main menu...")


def run_speed_to_lead():
    clear_console()
    print("=" * 65)
    print("       🎯 SWARM B: SPEED-TO-LEAD REAL ESTATE CONCIERGE 🎯")
    print("=" * 65)
    
    print("\nSelect a Lead Profile to simulate ingestion:")
    print("  1. Jane Smith (Zillow Lead - Active Buyer, relocating, Budget: $680k)")
    print("  2. Robert Chen (Facebook Ad Lead - Looking around, skeptical, unrepresented)")
    print("  3. Create Custom Lead Profile")
    print("-" * 65)
    
    choice = input("👉 Enter choice (1-3): ").strip()
    
    lead_id = f"lead_{uuid.uuid4().hex[:8]}"
    lead_profile = {}
    
    if choice == "1":
        lead_profile = {
            "name": "Jane Smith",
            "phone": "+1-555-0144",
            "email": "janesmith@gmail.com",
            "source": "Zillow Portal"
        }
    elif choice == "2":
        lead_profile = {
            "name": "Robert Chen",
            "phone": "+1-555-0811",
            "email": "robchen@gmail.com",
            "source": "Facebook Ad Form"
        }
    else:
        print("\n📝 CREATE CUSTOM LEAD PROFILE:")
        name = input("Lead Name : ") or "Custom Client"
        phone = input("Phone Number : ") or "+1-555-0000"
        email = input("Email Address: ") or "client@gmail.com"
        source = input("Lead Source (e.g. Website, Realtor): ") or "Manual Ingest"
        lead_profile = {
            "name": name,
            "phone": phone,
            "email": email,
            "source": source
        }

    clear_console()
    print("=" * 65)
    print("📲             SIMULATED SMS LEAD CHAT CONSOLE             📲")
    print("=" * 65)
    print(f" Client Profile:")
    print(f"  - Name  : {lead_profile['name']}")
    print(f"  - Phone : {lead_profile['phone']}")
    print(f"  - Email : {lead_profile['email']}")
    print(f"  - Source: {lead_profile['source']}")
    print("-" * 65)
    print("  Initializing lead profile, enriching data, and sending Outreach SMS...")
    print("-" * 65)

    # 1. Trigger Initial Outreach
    concierge_text = process_incoming_message(lead_id, lead_profile)
    print(f"\n💬 [Agent SMS Outreach]: \"{concierge_text}\"")
    print("-" * 65)

    # Enter conversational loop
    while True:
        user_message = input(f"\n📨 [{lead_profile['name']} Reply] (or type 'exit' to score & sync): \n👉 ").strip()
        
        if not user_message:
            continue
            
        if user_message.lower() in ["exit", "quit", "score"]:
            break
            
        print("\n⏳ Agent is replying...")
        agent_reply = process_incoming_message(lead_id, lead_profile, user_reply=user_message)
        print(f"\n💬 [Agent SMS Reply]: \"{agent_reply}\"")
        print("-" * 65)

    # Display final scored output
    print("\n⏳ Compiling final qualification rubrics and checking CRM Database...")
    print("-" * 65)
    
    # Read lead from outputs/crm_leads.json
    crm_file_path = "outputs/crm_leads.json"
    if os.path.exists(crm_file_path):
        try:
            with open(crm_file_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            lead_data = records.get(lead_id)
            if lead_data:
                print("\n" + "=" * 65)
                print("🏆                  QUALIFICATION CRM SCORECARD                  🏆")
                print("=" * 65)
                print(f" Client Name   : {lead_data['name']}")
                print(f" Ingestion ID  : {lead_data['lead_id']}")
                print(f" Final Score   : ⭐ {lead_data['final_score']}/10.0")
                print(f" Status        : 🚦 {lead_data['status'].upper()}")
                print("-" * 65)
                print(" 📊 Qualification Subscores:")
                for dimension, score in lead_data.get("scores", {}).items():
                    print(f"  - {dimension.upper():<15}: {score}/10.0")
                print("-" * 65)
                print(f" 📂 Zillow Enrichment Context:\n{lead_data['enriched_info']}")
                print("=" * 65)
                print(f"  🟢 CRM File Updated: {crm_file_path}")
                print("=" * 65)
        except Exception as e:
            print(f"⚠️ Error reading CRM data scorecard: {e}")
    else:
        print("❌ Error: No CRM data saved!")

    input("\nPress Enter to return to main menu...")


def main():
    # Ensure outputs/ directory exists
    os.makedirs("outputs", exist_ok=True)
    
    while True:
        clear_console()
        print_header()
        print("Please choose an option:")
        print("  1. Run Speed-To-Lead (Simulate Interactive Buyer Qualification Chat)")
        print("  2. Exit Suite")
        print("-" * 65)
        
        choice = input("👉 Enter choice (1-2): ").strip()
        
        if choice == "1":
            run_speed_to_lead()
        elif choice == "2":
            clear_console()
            print("\n👋 Thank you for using PresenceIX Swarm Orchestrator. Good luck on the Agent Pitch!")
            print("=============================================================\n")
            break
        else:
            print("❌ Invalid selection. Please enter 1 or 2.")
            import time
            time.sleep(1.5)


if __name__ == "__main__":
    main()
