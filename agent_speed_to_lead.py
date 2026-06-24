import os
import json
from datetime import datetime
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv

# Load credentials
load_dotenv()

from llm_router import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
try:
    from langgraph.checkpoint.postgres import PostgresSaver
except ImportError:
    PostgresSaver = None

# ==========================================
# 1. DEFINE STATE (THE CLIPBOARD)
# ==========================================
class SpeedToLeadState(TypedDict):
    lead_id: str                      # Unique ID for the lead
    name: str                         # Lead name
    phone: str                        # Lead phone number
    email: str                        # Lead email
    source: str                       # Where the lead came from (e.g. Zillow, Facebook Ads)
    enriched_info: str                # Enriched buyer search preferences or property data
    dialog_history: List[Dict[str, str]] # SMS chat history [{"role": "agent"/"user", "content": "text"}]
    scores: Dict[str, float]          # Rubric subscores: budget, timeline, motivation, representation
    final_score: float                # Final 1-10 overall score
    status: str                       # IN_PROGRESS, QUALIFIED, NURTURE, DISQUALIFIED
    logs: List[str]                   # Internal execution history log

# ==========================================
# 2. DEFINE AGENT NODES
# ==========================================

def orchestrator_router(state: SpeedToLeadState) -> dict:
    """
    Decides whether this is a brand new lead ingestion or an ongoing text dialog.
    """
    history = state.get("dialog_history", []) or []
    print(f"\n🚦 [Speed-To-Lead -> Router] Incoming session trigger. Chat history length: {len(history)}")
    return {}


def route_lead_path(state: SpeedToLeadState) -> str:
    history = state.get("dialog_history", []) or []
    if not history:
        print("🚦 [Speed-To-Lead -> Router] Route: No history found. Routing to 'enricher' for outreach.")
        return "enricher"
    else:
        print("🚦 [Speed-To-Lead -> Router] Route: Lead responded. Routing to 'qualifier' for dialog.")
        return "qualifier"


def enrich_lead_node(state: SpeedToLeadState) -> dict:
    """
    Enricher Node: Combines live Hunter.io email verification (via Composio)
    with simulated Zillow property-search profiles for real estate context.
    """
    name = state.get("name", "Valued Client")
    email = state.get("email", "")
    source = state.get("source", "Web Form")
    print(f"\n📂 [Speed-To-Lead -> Enricher] Enriching lead profile for {name} from {source}...")
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append(f"Enricher started at {datetime.now().strftime('%H:%M:%S')}")
    
    # 1. Base property search profile generation
    try:
        llm = get_llm(temperature=0.2)
        prompt = (
            f"You are a real estate enrichment assistant (simulating Zillow/Redfin lookup).\n"
            f"The lead is: Name={name}, Source={source}.\n\n"
            f"Generate a realistic property-search profile for them including:\n"
            f"1. A simulated property address they recently clicked (e.g. '1428 Elm Street').\n"
            f"2. A realistic median home price in that neighborhood (e.g. '$650,000').\n"
            f"3. Expected buyer profile (e.g. local upgrade seeker, relocation buyer)."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        enriched = response.content
        print("🟢 [Enricher] Simulated Zillow real estate profile compiled.")
    except Exception as e:
        print(f"⚠️ [Enricher Node] LLM Error: {e}. Falling back to default.")
        enriched = f"Mock enrichment for {name}: Interest in 3-bed home near active schools, $500k range."

    # 2. Try Live Hunter.io verification via Composio if configured
    hunter_log_data = ""
    composio_api_key = os.getenv("COMPOSIO_API_KEY")
    if composio_api_key and "your_key" not in composio_api_key and email:
        try:
            print(f"🔌 [Enricher] Connecting to Hunter.io via Composio to verify: '{email}'")
            from composio import Composio
            from composio_langgraph import LanggraphProvider
            
            # Initialize Composio Session
            composio = Composio(provider=LanggraphProvider())
            session = composio.create(user_id="presenceix_lead_session")
            
            # Query hunter tools specifically via top-level sdk since session.tools() only returns base meta-tools in modern Composio
            hunter_tools = composio.tools.get(user_id="presenceix_lead_session", toolkits=["hunter"])
            if hunter_tools:
                print(f"🟢 [Enricher] Live Hunter.io connector active! Found {len(hunter_tools)} actions.")
                
                # Match verifier or fallback to first tool
                verifier_action = next((getattr(t, "name", getattr(t, "slug", str(t))) for t in hunter_tools if "verifier" in getattr(t, "name", "").lower() or "verify" in getattr(t, "name", "").lower()), None)
                if not verifier_action:
                    verifier_action = getattr(hunter_tools[0], "name", getattr(hunter_tools[0], "slug", str(hunter_tools[0])))
                    
                print(f"⚡ [Enricher] Executing live Hunter action: '{verifier_action}'")
                # Direct trigger using modern Composio Session execution
                action_result = session.execute(tool_slug=verifier_action, arguments={"email": email})
                
                # Convert response to dictionary safely
                if hasattr(action_result, "model_dump"):
                    result_dict = action_result.model_dump()
                elif hasattr(action_result, "dict"):
                    result_dict = action_result.dict()
                elif isinstance(action_result, dict):
                    result_dict = action_result
                else:
                    result_dict = {}
                
                # Parse verification score & deliverability
                hunter_log_data = f"\n\n--- 🕵️‍♂️ LIVE HUNTER.IO CONTACT VERIFICATION ---\n"
                hunter_log_data += f"Email Address  : {email}\n"
                
                # Check for standard Hunter output structure
                data_payload = result_dict.get("data", {})
                if isinstance(data_payload, dict) and "data" in data_payload:
                    data_payload = data_payload.get("data", {})
                    
                if data_payload:
                    hunter_log_data += f"Deliverability : {str(data_payload.get('result', 'unknown')).upper()}\n"
                    hunter_log_data += f"Confidence Score: {data_payload.get('score', 0)}%\n"
                    hunter_log_data += f"Disposable Email: {'Yes' if data_payload.get('disposable') else 'No'}\n"
                    hunter_log_data += f"Web Presence   : Found {len(data_payload.get('sources', []))} public citations.\n"
                else:
                    try:
                        hunter_log_data += f"Raw Output: {json.dumps(result_dict, indent=2)}\n"
                    except Exception:
                        hunter_log_data += f"Raw Output: {str(action_result)}\n"
                    
                print("🟢 [Enricher] Hunter.io verification result added to state.")
                new_logs.append("Live Hunter.io verification successful.")
            else:
                print("⚠️ [Enricher] Hunter.io app is connected in dashboard but no actions returned in session.")
        except Exception as e:
            print(f"⚠️ [Enricher] Hunter.io lookup encountered an exception: {e}")
            new_logs.append(f"Hunter lookup bypassed due to error: {e}")

    # Merge profiles
    final_enriched = enriched + hunter_log_data
    print("🟢 [Speed-To-Lead -> Enricher] Lead enrichment complete.")
    
    new_logs.append("Lead profile enriched.")
    return {
        "enriched_info": final_enriched,
        "logs": new_logs
    }


def outreach_node(state: SpeedToLeadState) -> dict:
    """
    Outreach Node: Sends the immediate, 60-second warm greeting SMS.
    """
    name = state.get("name", "there")
    enriched = state.get("enriched_info", "")
    print(f"\n💬 [Speed-To-Lead -> Outreach] Drafting 60-second instant SMS outreach...")
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append(f"Outreach node drafted message at {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        llm = get_llm(temperature=0.7)
        prompt = (
            f"You are a warm, highly professional real estate concierge at PresenceIX.\n"
            f"Draft an instant, conversational SMS greeting for lead: '{name}'.\n"
            f"Use this enriched background to make it personal:\n{enriched}\n\n"
            f"Rules:\n"
            f"- Keep it strictly under 140 characters.\n"
            f"- Mention the property address or local neighborhood from the enrichment.\n"
            f"- Ask a single natural, low-friction question (e.g. 'Looking to move soon or just browsing?').\n"
            f"- Do NOT sound salesy or robotic."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        sms_greeting = response.content.strip().replace('"', '')
        print(f"🟢 [Outreach SMS Sent]: \"{sms_greeting}\"")
    except Exception as e:
        print(f"⚠️ [Outreach Node] Error: {e}")
        sms_greeting = f"Hi {name}! I saw you clicked on a property in the area. Are you looking to move soon or just browsing?"
        
    # Append to dialog history
    history = list(state.get("dialog_history", []) or [])
    history.append({"role": "agent", "content": sms_greeting})
    
    # Send client SMS and beautiful Admin alert notification if configured
    try:
        from notifications import send_client_sms, notify_admin_new_lead
        recipient_phone = state.get("phone", "")
        send_client_sms(sms_greeting, recipient_phone)
        notify_admin_new_lead(
            lead_id=state.get("lead_id", "unknown"),
            name=name,
            phone=recipient_phone,
            email=state.get("email", ""),
            source=state.get("source", ""),
            enriched_info=state.get("enriched_info", ""),
            initial_greeting=sms_greeting
        )
    except Exception as e:
        print(f"⚠️ [Outreach Node] Notification trigger error: {e}")
        
    new_logs.append("Initial outreach SMS appended.")
    return {
        "dialog_history": history,
        "status": "IN_PROGRESS",
        "logs": new_logs
    }


def qualifier_node(state: SpeedToLeadState) -> dict:
    """
    Qualifier Node: Manages conversational response back to lead replies.
    Probes gently for missing qualifying dimensions.
    """
    name = state.get("name", "there")
    enriched = state.get("enriched_info", "")
    history = state.get("dialog_history", []) or []
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append(f"Qualifier node evaluated at {datetime.now().strftime('%H:%M:%S')}")

    # Check if the latest user message is an exit trigger to score the lead
    is_exit_trigger = False
    if history:
        last_msg = history[-1]
        if last_msg.get("role") == "user" and last_msg.get("content", "").lower().strip() in ["exit", "quit", "score"]:
            is_exit_trigger = True

    if is_exit_trigger:
        print("ℹ️ [Qualifier Node] Exit trigger detected. Skipping conversational agent SMS response drafting.")
        new_logs.append("Qualifier node skipped: exit trigger detected.")
        return {
            "logs": new_logs
        }
    
    print("\n💬 [Speed-To-Lead -> Qualifier] Analyzing lead response & drafting reply...")
    
    # Format dialog transcript for LLM
    formatted_history = ""
    for msg in history:
        role_label = "Agent" if msg["role"] == "agent" else "Client"
        formatted_history += f"{role_label}: {msg['content']}\n"
        
    try:
        llm = get_llm(temperature=0.5)
        prompt = (
            f"You are a world-class conversational real estate qualifying agent for PresenceIX.\n"
            f"The lead is: '{name}'. Context details: '{enriched}'.\n\n"
            f"Transcript history:\n{formatted_history}\n"
            f"Goal: Qualify the lead on these 4 dimensions:\n"
            f"1. Budget (What price range are they targeting?)\n"
            f"2. Timeline (When do they want to purchase/move?)\n"
            f"3. Motivation (Why are they buying? Job relocation, expanding, renting to buying?)\n"
            f"4. Agent Representation (Are they already working with another agent exclusive contract?)\n\n"
            f"Task:\n"
            f"- Draft a friendly, supportive SMS response to the client's last message.\n"
            f"- Acknowledge their response warmly.\n"
            f"- Gently ask for **only ONE** of the missing dimensions that they haven't answered yet.\n"
            f"- Keep it strictly conversational and under 160 characters. Do NOT sound like an interrogation form!"
        )
        response = llm.invoke([
            SystemMessage(content="You are a warm, helpful real estate agent. Keep responses punchy and SMS-friendly."),
            HumanMessage(content=prompt)
        ])
        reply = response.content.strip().replace('"', '')
        print(f"🟢 [Agent SMS Reply]: \"{reply}\"")
    except Exception as e:
        print(f"⚠️ [Qualifier Node] Error: {e}")
        reply = f"Thanks for sharing that, {name}! What kind of budget or price range are you hoping to stay under?"
        
    history.append({"role": "agent", "content": reply})
    
    # Send conversational SMS to client via WhatsApp only (bypass Telegram/Slack admin channels)
    try:
        from notifications import send_client_sms
        recipient_phone = state.get("phone", "")
        send_client_sms(reply, recipient_phone)
    except Exception as e:
        print(f"⚠️ [Qualifier Node] Notification trigger error: {e}")
        
    new_logs.append("Qualifier reply appended.")
    return {
        "dialog_history": history,
        "logs": new_logs
    }


def scorer_node(state: SpeedToLeadState) -> dict:
    """
    Scorer Node: Uses an LLM real-estate rubric to evaluate the dialog history,
    generate sub-scores (1-10) and update overall qualification score and status.
    """
    history = state.get("dialog_history", []) or []
    print("\n📊 [Speed-To-Lead -> Scorer] Scoring lead qualification (1-10) using conversational rubric...")
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append(f"Scorer evaluated at {datetime.now().strftime('%H:%M:%S')}")
    
    # Format dialog transcript for LLM
    formatted_history = ""
    for msg in history:
        role_label = "Agent" if msg["role"] == "agent" else "Client"
        formatted_history += f"{role_label}: {msg['content']}\n"
        
    default_scores = {"budget": 1.0, "timeline": 1.0, "motivation": 1.0, "representation": 10.0}
    final_score = 1.0
    status = "IN_PROGRESS"
    
    try:
        llm = get_llm(temperature=0.1)
        prompt = (
            f"Analyze this real estate conversation and score the client on four qualifying dimensions (each from 1.0 to 10.0):\n\n"
            f"Transcript:\n{formatted_history}\n\n"
            f"Scoring Rubric:\n"
            f"1. BUDGET (10.0 = Stated clearly and exceeds $500k. 5.0 = Stated budget under $300k. 1.0 = Refused to answer/unknown.)\n"
            f"2. TIMELINE (10.0 = Ready to move/buy in <30 days. 5.0 = Looking at 6+ months out. 1.0 = No timeline/window shopping.)\n"
            f"3. MOTIVATION (10.0 = Urgent, logical reason (job relocation, growing family, renting lease ends). 5.0 = Low interest. 1.0 = Accident click.)\n"
            f"4. REPRESENTATION (10.0 = Unrepresented - we can capture them! 1.0 = Already signed a binding contract with another broker.)\n\n"
            f"Task: Output a raw JSON object containing exactly these fields:\n"
            f"{{\n"
            f"  \"budget\": float,\n"
            f"  \"timeline\": float,\n"
            f"  \"motivation\": float,\n"
            f"  \"representation\": float,\n"
            f"  \"final_score\": float (average of the 4 dimensions),\n"
            f"  \"status\": \"QUALIFIED\" / \"NURTURE\" / \"DISQUALIFIED\"\n"
            f"}}\n"
            f"Note:\n"
            f"- If final_score >= 7.0, status is \"QUALIFIED\".\n"
            f"- If final_score between 4.0 and 6.9, status is \"NURTURE\".\n"
            f"- If final_score <= 3.9, status is \"DISQUALIFIED\".\n"
            f"- Return ONLY the raw JSON block without markdown formatting."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        raw_content = response.content.strip()
        
        # Clean any markdown fences
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].strip()
            
        scoring_data = json.loads(raw_content)
        
        default_scores = {
            "budget": scoring_data.get("budget", 1.0),
            "timeline": scoring_data.get("timeline", 1.0),
            "motivation": scoring_data.get("motivation", 1.0),
            "representation": scoring_data.get("representation", 10.0)
        }
        final_score = scoring_data.get("final_score", 1.0)
        status = scoring_data.get("status", "IN_PROGRESS")
        print(f"🟢 [Scorer Result] Final Score: {final_score}/10 | Status: {status}")
    except Exception as e:
        print(f"⚠️ [Scorer Node] Error parsing scoring: {e}. Defaulting values.")
        
    # Send qualification assessment update alert to admin (Telegram/Slack) ONLY when forced/final scoring (i.e. last user message was "exit", "quit", or "score")
    is_exit_trigger = False
    if history:
        for msg in reversed(history):
            if msg.get("role") == "user":
                if msg.get("content", "").lower().strip() in ["exit", "quit", "score"]:
                    is_exit_trigger = True
                break

    if is_exit_trigger:
        try:
            from notifications import notify_admin_assessment
            # Extract latest user message and agent response from history
            latest_client_msg = "N/A"
            agent_response = "N/A"
            if history:
                # Find last agent response
                for msg in reversed(history):
                    if msg["role"] == "agent":
                        agent_response = msg["content"]
                        break
                # Find last client message (the one before "exit", or "exit" itself if none before)
                found_user_msg = False
                for msg in reversed(history):
                    if msg["role"] == "user" and msg["content"].lower().strip() not in ["exit", "quit", "score"]:
                        latest_client_msg = msg["content"]
                        found_user_msg = True
                        break
                if not found_user_msg:
                    # Fallback to the exit message itself
                    for msg in reversed(history):
                        if msg["role"] == "user":
                            latest_client_msg = msg["content"]
                            break
                        
            notify_admin_assessment(
                lead_id=state.get("lead_id", "unknown"),
                name=state.get("name", "there"),
                final_score=final_score,
                scores=default_scores,
                status=status,
                latest_client_msg=latest_client_msg,
                agent_response=agent_response
            )
        except Exception as e:
            print(f"⚠️ [Scorer Node] Admin notification trigger error: {e}")
    else:
        print("ℹ️ [Scorer Node] Conversational back-and-forth scoring run; skipping admin notification to prevent spam.")

    new_logs.append(f"Scored lead final_score={final_score}")
    return {
        "scores": default_scores,
        "final_score": final_score,
        "status": status,
        "logs": new_logs
    }


def crm_sync_node(state: SpeedToLeadState) -> dict:
    """
    CRM Sync Node: Logs lead records to local CRM simulation file and
    syncs them to Airtable CRM in real-time if configured.
    """
    print("\n💾 [Speed-To-Lead -> Sync] Logging updated lead scores to PresenceIX CRM simulation...")
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append(f"CRM Sync initiated at {datetime.now().strftime('%H:%M:%S')}")
    
    # Load existing CRM or create new
    crm_file_path = "outputs/crm_leads.json"
    os.makedirs("outputs", exist_ok=True)
    
    crm_records = {}
    if os.path.exists(crm_file_path):
        try:
            with open(crm_file_path, "r", encoding="utf-8") as f:
                crm_records = json.load(f)
        except Exception:
            crm_records = {}
            
    lead_id = state.get("lead_id", "unknown_lead")
    
    payload = {
        "lead_id": lead_id,
        "name": state.get("name", ""),
        "phone": state.get("phone", ""),
        "email": state.get("email", ""),
        "source": state.get("source", ""),
        "enriched_info": state.get("enriched_info", ""),
        "dialog_history": state.get("dialog_history", []),
        "scores": state.get("scores", {}),
        "final_score": state.get("final_score", 1.0),
        "status": state.get("status", ""),
        "last_sync": datetime.now().isoformat()
    }
    
    crm_records[lead_id] = payload
    
    # 1. Local backup sync
    try:
        with open(crm_file_path, "w", encoding="utf-8") as f:
            json.dump(crm_records, f, indent=4, ensure_ascii=False)
        print(f"🟢 [Speed-To-Lead -> Sync] Success! Synced Lead '{lead_id}' to local backup: '{crm_file_path}'")
        new_logs.append(f"CRM Local Sync successful.")
    except Exception as e:
        print(f"❌ [CRM Sync] Failed to save local backup: {e}")
        new_logs.append(f"CRM Local Sync failed: {e}")
        
    # 2. Live Airtable sync
    try:
        from airtable_sync import sync_lead_to_airtable, is_airtable_configured
        if is_airtable_configured():
            print(f"⚡ [CRM Sync] Attempting live Airtable CRM sync for '{lead_id}'...")
            success = sync_lead_to_airtable(payload)
            if success:
                new_logs.append("Airtable Sync successful.")
            else:
                new_logs.append("Airtable Sync attempted but failed.")
        else:
            new_logs.append("Airtable Sync skipped (credentials not configured).")
    except Exception as e:
        print(f"⚠️ [CRM Sync] Airtable import or execution error: {e}")
        new_logs.append(f"Airtable Sync error: {e}")
        
    return {
        "logs": new_logs
    }

# ==========================================
# 3. BUILD THE STATE GRAPH FLOW
# ==========================================

def get_speed_to_lead_graph(checkpointer=None):
    """
    Compiles and returns the Speed-To-Lead LangGraph.
    Uses SQLite database checkpointing for conversation persistence.
    """
    workflow = StateGraph(SpeedToLeadState)
    
    # Register our nodes
    workflow.add_node("orchestrator", orchestrator_router)
    workflow.add_node("enricher", enrich_lead_node)
    workflow.add_node("outreach", outreach_node)
    workflow.add_node("qualifier", qualifier_node)
    workflow.add_node("scorer", scorer_node)
    workflow.add_node("sync", crm_sync_node)
    
    # Entry point
    workflow.set_entry_point("orchestrator")
    
    # Conditional edge from orchestrator: Decide to enrich + outreach or to qualify
    workflow.add_conditional_edges(
        "orchestrator",
        route_lead_path,
        {
            "enricher": "enricher",
            "qualifier": "qualifier"
        }
    )
    
    # Ingestion flow
    workflow.add_edge("enricher", "outreach")
    workflow.add_edge("outreach", "sync")
    
    # Interactive flow
    workflow.add_edge("qualifier", "scorer")
    workflow.add_edge("scorer", "sync")
    
    # Final node is sync
    workflow.add_edge("sync", END)
    
    return workflow.compile(checkpointer=checkpointer)


# ==========================================
# 4. INTERACTIVE CLIENT SESSION RUNNER
# ==========================================
def process_incoming_message(lead_id: str, lead_info: dict, user_reply: str = None, db_path: str = "presenceix_memory.sqlite") -> str:
    """
    Helper function to wrap LangGraph call. Loads history, appends user reply,
    runs the swarm, and returns the agent response.
    """
    config = {"configurable": {"thread_id": lead_id}}
    
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    
    if database_url and PostgresSaver is not None:
        print(f"🔌 [Saver] Connecting to production PostgresSaver (DATABASE_URL)...")
        saver_context = PostgresSaver.from_conn_string(database_url)
    else:
        print(f"🔌 [Saver] Connecting to local SqliteSaver ({db_path})...")
        saver_context = SqliteSaver.from_conn_string(db_path)
        
    with saver_context as memory:
        if database_url and PostgresSaver is not None:
            memory.setup()
            
        app = get_speed_to_lead_graph(checkpointer=memory)
        
        # Check current state
        current_state = app.get_state(config)
        
        # If empty, initialize lead ingestion
        if not current_state.values:
            print(f"🎬 [CRM System] New lead received. ID: {lead_id}. Starting Ingestion & Outreach...")
            initial_state = {
                "lead_id": lead_id,
                "name": lead_info.get("name", "there"),
                "phone": lead_info.get("phone", ""),
                "email": lead_info.get("email", ""),
                "source": lead_info.get("source", "Zillow"),
                "enriched_info": "",
                "dialog_history": [],
                "scores": {},
                "final_score": 1.0,
                "status": "IN_PROGRESS",
                "logs": []
            }
            app.invoke(initial_state, config=config)
            
            # Reload state to fetch drafted outreach
            current_state = app.get_state(config)
            
        elif user_reply:
            print(f"📨 [CRM System] Client ID: {lead_id} Replied: \"{user_reply}\"")
            
            # Extract state values and update dialog history with user message
            state_vals = dict(current_state.values)
            history = list(state_vals.get("dialog_history", []) or [])
            history.append({"role": "user", "content": user_reply})
            
            # Run graph to qualify and score
            app.invoke({"dialog_history": history}, config=config)
            
            # Reload state
            current_state = app.get_state(config)
            
        # Extract the latest agent reply
        updated_history = current_state.values.get("dialog_history", [])
        if updated_history and updated_history[-1]["role"] == "agent":
            return updated_history[-1]["content"]
        return "Hi there! I will connect you with an agent shortly."


if __name__ == "__main__":
    print("=" * 65)
    print("      🎯 PRESENCEIX SPEED-TO-LEAD INDEPENDENT TESTER 🎯")
    print("=" * 65)
    
    test_id = "lead_john_doe_99"
    test_profile = {
        "name": "John Doe",
        "phone": "+1-555-0199",
        "email": "johndoe@gmail.com",
        "source": "Zillow Portal"
    }
    
    # 1. Simulate lead ingestion & initial outreach greeting
    concierge_text = process_incoming_message(test_id, test_profile)
    print(f"\n📲 [Lead Phone Display]: MESSAGE RECEIVED FROM AGENT:\n\"{concierge_text}\"")
    print("-" * 65)
    
    # 2. Simulate User response 1
    reply_1 = "I am actually looking for a 3-bedroom around $680k, ready to buy in a month."
    agent_reply_1 = process_incoming_message(test_id, test_profile, user_reply=reply_1)
    print(f"\n📲 [Lead Phone Display]: MESSAGE RECEIVED FROM AGENT:\n\"{agent_reply_1}\"")
    print("-" * 65)
    
    # 3. Simulate User response 2 (Qualification complete)
    reply_2 = "We are relocating from Boston and we do not have an agent contract signed yet."
    agent_reply_2 = process_incoming_message(test_id, test_profile, user_reply=reply_2)
    print(f"\n📲 [Lead Phone Display]: MESSAGE RECEIVED FROM AGENT:\n\"{agent_reply_2}\"")
    print("=" * 65)
