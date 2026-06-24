import os
import json
from datetime import datetime
from typing import TypedDict, List
from dotenv import load_dotenv

# Load credentials
load_dotenv()

from llm_router import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# ==========================================
# 1. DEFINE STATE (THE CLIPBOARD)
# ==========================================
class ContentBrainState(TypedDict):
    topic: str               # The core topic/theme to write content about
    research_notes: str      # Raw facts, stats, and trending data collected
    linkedin_draft: str      # Finished professional long-form LinkedIn post
    x_thread: str            # Finished high-engagement viral Twitter thread
    video_script: str        # Finished TikTok/Reels short-form video script
    logs: List[str]          # Activity history log

# ==========================================
# 2. DEFINE AGENT NODES
# ==========================================

def researcher_node(state: ContentBrainState) -> dict:
    """
    Research Node: Gathers hot trends, statistics, and educational facts on the topic.
    """
    topic = state["topic"]
    print(f"\n🔍 [Content Brain -> Researcher] Gathering deep research and trends for: '{topic}'")
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append(f"Researcher started gathering facts at {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        # Get cheap/smart LLM from our unified router
        llm = get_llm(temperature=0.4)
        
        prompt = (
            f"You are a leading growth marketer and research analyst. "
            f"Perform extensive, detailed research on the topic: '{topic}'.\n\n"
            f"Compile:\n"
            f"1. At least 3 eye-opening statistics or facts (with simulated citations).\n"
            f"2. Core pain points or challenges related to this topic.\n"
            f"3. Practical solutions or actionable insights.\n\n"
            f"Keep it extremely structured and dense with high-quality insights."
        )
        
        response = llm.invoke([
            SystemMessage(content="You are an expert research analyst compiling industry insights."),
            HumanMessage(content=prompt)
        ])
        research_data = response.content
        print("🔍 [Content Brain -> Researcher] Finished research compiling.")
    except Exception as e:
        print(f"⚠️ [Researcher Node] Error in LLM connection: {e}. Falling back to default data.")
        research_data = (
            f"Mock Research Data for '{topic}':\n"
            f"- Stat: 82% of target audience engages more with automation insights.\n"
            f"- Pain Point: Operational friction and lack of execution consistency.\n"
            f"- Solution: Build modular agent swarms that automate content & qualify leads."
        )
        
    new_logs.append("Researcher finished compiling facts.")
    return {
        "research_notes": research_data,
        "logs": new_logs
    }


def linkedin_node(state: ContentBrainState) -> dict:
    """
    LinkedIn Node: Formats professional long-form posts with line breaks and industry framing.
    """
    topic = state["topic"]
    notes = state.get("research_notes", "")
    print("\n✍️ [Content Brain -> LinkedIn Writer] Crafting professional LinkedIn post...")
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append(f"LinkedIn writer started at {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        llm = get_llm(temperature=0.7)
        prompt = (
            f"You are a world-class copywriter specializing in LinkedIn content. "
            f"Draft a high-converting, professional, and educational LinkedIn post about '{topic}'.\n\n"
            f"Use these research notes for facts and data:\n{notes}\n\n"
            f"Structuring rules:\n"
            f"- Start with a compelling, single-sentence hook.\n"
            f"- Break text into short, single-sentence paragraphs with clear vertical spacing.\n"
            f"- Use bullet points for readability.\n"
            f"- Conclude with an engaging question to drive comments (Call-To-Action).\n"
            f"- Add 3-5 relevant, professional hashtags at the end."
        )
        
        response = llm.invoke([
            SystemMessage(content="You are a LinkedIn personal brand builder and elite content strategist."),
            HumanMessage(content=prompt)
        ])
        draft = response.content
        print("🟢 [Content Brain -> LinkedIn Writer] LinkedIn post draft complete.")
    except Exception as e:
        print(f"⚠️ [LinkedIn Node] Error: {e}")
        draft = f"LinkedIn placeholder copy for '{topic}'."
        
    return {
        "linkedin_draft": draft
    }


def x_node(state: ContentBrainState) -> dict:
    """
    X Thread Node: Formats viral threads with high engagement hooks and numbering.
    """
    topic = state["topic"]
    notes = state.get("research_notes", "")
    print("\n⚡ [Content Brain -> X Thread Writer] Crafting viral Twitter/X thread...")
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append(f"X thread writer started at {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        llm = get_llm(temperature=0.8)
        prompt = (
            f"You are a master X (Twitter) ghostwriter specializing in viral educational threads.\n"
            f"Convert this topic: '{topic}' and these facts:\n{notes}\n\n"
            f"Write an educational X thread of exactly 4 to 6 tweets.\n\n"
            f"Structuring rules:\n"
            f"- Tweet 1 (Hook): Must be extremely punchy, promise high value, and encourage clicking to read the thread.\n"
            f"- Tweet 2-5 (Body): Deliver the insights, statistics, and step-by-step solutions. Use numbers (e.g. 1/5, 2/5, etc.) and list bullet points.\n"
            f"- Tweet 6 (CTA): Conclude with a strong call-to-action (e.g. 'If you found this thread valuable, follow @PresenceIX and retweet the first post').\n"
            f"- Ensure every individual tweet stays strictly under 280 characters."
        )
        
        response = llm.invoke([
            SystemMessage(content="You are an elite X (Twitter) strategist who builds viral educational threads."),
            HumanMessage(content=prompt)
        ])
        draft = response.content
        print("🟢 [Content Brain -> X Thread Writer] X Thread draft complete.")
    except Exception as e:
        print(f"⚠️ [X Thread Node] Error: {e}")
        draft = f"X Thread placeholder for '{topic}'."
        
    return {
        "x_thread": draft
    }


def video_node(state: ContentBrainState) -> dict:
    """
    Video Script Node: Generates short-form video scripts (TikTok/Reel) with video/audio cues.
    """
    topic = state["topic"]
    notes = state.get("research_notes", "")
    print("\n🎬 [Content Brain -> Video Scriptwriter] Creating TikTok/Reels short-form script...")
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append(f"Video scriptwriter started at {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        llm = get_llm(temperature=0.7)
        prompt = (
            f"You are an expert video director and short-form content creator for TikTok and Instagram Reels.\n"
            f"Draft a high-retention 30-60 second video script about: '{topic}'.\n\n"
            f"Utilize these points:\n{notes}\n\n"
            f"Structuring rules:\n"
            f"- Hook (0-3 seconds): Must be a scroll-stopping visual and voice hook.\n"
            f"- Format the script into a table or clear block layout showing: [VISUAL CUE / B-ROLL] and [SPEAKER VOICEOVER].\n"
            f"- Ensure the pacing is rapid, conversational, and energetic.\n"
            f"- Add a 1-sentence micro-hook in the middle to prevent swipe-away.\n"
            f"- Conclude with a clear, fast CTA (e.g. 'Read the caption to get our free automation guide!')."
        )
        
        response = llm.invoke([
            SystemMessage(content="You are a master of short-form vertical video scripting and video direction."),
            HumanMessage(content=prompt)
        ])
        draft = response.content
        print("🟢 [Content Brain -> Video Scriptwriter] Video script complete.")
    except Exception as e:
        print(f"⚠️ [Video Node] Error: {e}")
        draft = f"Video script placeholder for '{topic}'."
        
    return {
        "video_script": draft
    }


def exporter_node(state: ContentBrainState) -> dict:
    """
    Exporter Node: Joins the parallel threads, compiles drafts, saves them locally,
    and syncs them to Airtable Content Calendar in real-time if configured.
    """
    print("\n💾 [Content Brain -> Exporter] Joining drafts and saving to output pipeline...")
    
    logs = state.get("logs", []) or []
    new_logs = list(logs)
    new_logs.append("LinkedIn, X, and TikTok/Reel copywriting nodes executed in parallel.")
    new_logs.append(f"Exporter initiated at {datetime.now().strftime('%H:%M:%S')}")
    
    # Compile payload
    payload = {
        "topic": state["topic"],
        "generated_at": datetime.now().isoformat(),
        "research_notes": state.get("research_notes", ""),
        "linkedin_draft": state.get("linkedin_draft", ""),
        "x_thread": state.get("x_thread", ""),
        "video_script": state.get("video_script", ""),
        "status": "DRAFT"
    }
    
    # Ensure outputs directory exists
    os.makedirs("outputs", exist_ok=True)
    
    # Save as JSON locally
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"outputs/content_draft_{timestamp}.json"
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        print(f"🟢 [Content Brain -> Exporter] Success! Saved content calendar draft locally to: '{file_path}'")
        new_logs.append(f"Exporter saved JSON file to {file_path}")
    except Exception as e:
        print(f"❌ [Exporter] Failed to write file: {e}")
        new_logs.append(f"Exporter failed to save file: {e}")
        
    # 2. Live Airtable Content Calendar sync
    try:
        from airtable_sync import sync_content_to_airtable, is_airtable_configured
        if is_airtable_configured():
            print(f"⚡ [Exporter] Attempting live Airtable Content Calendar sync...")
            success = sync_content_to_airtable(payload)
            if success:
                new_logs.append("Airtable Content Sync successful.")
            else:
                new_logs.append("Airtable Content Sync attempted but failed.")
        else:
            new_logs.append("Airtable Content Sync skipped (credentials not configured).")
    except Exception as e:
        print(f"⚠️ [Exporter] Airtable sync error: {e}")
        new_logs.append(f"Airtable sync error: {e}")
        
    return {
        "logs": new_logs
    }

# ==========================================
# 3. BUILD THE STATE GRAPH FLOW
# ==========================================

def get_content_brain_graph(checkpointer=None):
    """
    Compiles and returns the Content Brain LangGraph.
    Pass a valid SQLite or Memory checkpointer if state persistence is needed.
    """
    workflow = StateGraph(ContentBrainState)
    
    # Register our nodes
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("linkedin", linkedin_node)
    workflow.add_node("x_thread", x_node)
    workflow.add_node("video", video_node)
    workflow.add_node("exporter", exporter_node)
    
    # Set the starting node
    workflow.set_entry_point("researcher")
    
    # Wire up the fork-join (parallel execution)
    # Once researcher finishes, launch LinkedIn, X Thread, and Video Script generation in parallel
    workflow.add_edge("researcher", "linkedin")
    workflow.add_edge("researcher", "x_thread")
    workflow.add_edge("researcher", "video")
    
    # Once the parallel nodes complete, they all flow into the exporter
    workflow.add_edge("linkedin", "exporter")
    workflow.add_edge("x_thread", "exporter")
    workflow.add_edge("video", "exporter")
    
    # The exporter is the final node
    workflow.add_edge("exporter", END)
    
    return workflow.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    print("=" * 65)
    print("       🧠 PRESENCEIX CONTENT BRAIN INDEPENDENT TESTER 🧠")
    print("=" * 65)
    
    test_topic = "How multi-agent AI swarms are replacing single monolithic LLMs for sales pipelines."
    print(f"📋 Test Topic: '{test_topic}'")
    
    # Initialize state
    initial_state = {
        "topic": test_topic,
        "research_notes": "",
        "linkedin_draft": "",
        "x_thread": "",
        "video_script": "",
        "logs": []
    }
    
    # Run the graph with a test thread_id for SQLite memory
    config = {"configurable": {"thread_id": "test_content_session_1"}}
    
    print("\n⏳ Executing Content Brain LangGraph Swarm with SQLite Persistence...")
    with SqliteSaver.from_conn_string("presenceix_memory.sqlite") as memory:
        app = get_content_brain_graph(checkpointer=memory)
        final_output = app.invoke(initial_state, config=config)
    
    print("\n" + "=" * 65)
    print("🎉 CONTENT BRAIN TEST RUN COMPLETE!")
    print("=" * 65)
    print(f"\n📢 TOPIC: {final_output['topic']}")
    print("\n--- LINKEDIN DRAFT ---")
    print(final_output["linkedin_draft"][:300] + "...\n[Truncated for console]")
    print("\n--- X THREAD DRAFT ---")
    print(final_output["x_thread"][:300] + "...\n[Truncated for console]")
    print("\n--- VIDEO SCRIPT ---")
    print(final_output["video_script"][:300] + "...\n[Truncated for console]")
    print("\n" + "=" * 65)
    print("📊 ACTIVITY LOGS:")
    for idx, log in enumerate(final_output["logs"], 1):
        print(f"  {idx}. {log}")
    print("=" * 65)
