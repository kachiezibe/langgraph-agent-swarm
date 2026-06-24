import os
import sys
import uuid
import webbrowser
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environmental configurations
load_dotenv()

# Setup FastAPI App
app = FastAPI(title="PresenceIX Lead Simulation Hub")

# Try to import agent modules
try:
    from agent_speed_to_lead import process_incoming_message, get_speed_to_lead_graph
    from langgraph.checkpoint.sqlite import SqliteSaver
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
    except ImportError:
        PostgresSaver = None
except ImportError as e:
    print(f"❌ [Error] Failed to import agent modules: {e}")
    sys.exit(1)


class LeadSubmission(BaseModel):
    name: str
    phone: str
    email: str
    source: str
    notes: str = ""


class ChatMessage(BaseModel):
    lead_id: str
    message: str


def get_lead_state_from_sqlite(lead_id: str) -> dict:
    """Retrieves the full live state from LangGraph checkpointer (Postgres or SQLite)."""
    config = {"configurable": {"thread_id": lead_id}}
    
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    
    if database_url and PostgresSaver is not None:
        saver_context = PostgresSaver.from_conn_string(database_url)
    else:
        saver_context = SqliteSaver.from_conn_string("presenceix_memory.sqlite")
        
    try:
        with saver_context as memory:
            if database_url and PostgresSaver is not None:
                memory.setup()
            graph_app = get_speed_to_lead_graph(checkpointer=memory)
            state = graph_app.get_state(config)
            return dict(state.values) if state.values else {}
    except Exception as e:
        print(f"⚠️ Error fetching state from checkpointer: {e}")
        return {}


# Render HTML interface
@app.get("/", response_class=HTMLResponse)
async def get_index():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PresenceIX — Real Estate AI Lead Ingestion Simulator</title>
    <!-- Premium Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,400;0,500;1,400&family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #09090B;
            --bg-card: #121214;
            --bg-input: #18181B;
            --border-color: #27272A;
            --border-hover: #3F3F46;
            --primary: #1D9E75; /* Real Estate Emerald */
            --primary-glow: rgba(29, 158, 117, 0.15);
            --primary-text: #34D399;
            --text-main: #F4F4F5;
            --text-muted: #A1A1AA;
            --text-dark: #71717A;
            --accent-blue: #3B82F6;
            --accent-orange: #F59E0B;
            --accent-red: #EF4444;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        /* Ambient Glow Background Backgrounds */
        .ambient-glow-1 {
            position: absolute;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(29, 158, 117, 0.08) 0%, rgba(0,0,0,0) 70%);
            top: -100px;
            right: -100px;
            z-index: -1;
            pointer-events: none;
        }

        .ambient-glow-2 {
            position: absolute;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.04) 0%, rgba(0,0,0,0) 70%);
            bottom: -200px;
            left: -200px;
            z-index: -1;
            pointer-events: none;
        }

        /* Header Style */
        header {
            border-bottom: 1px solid var(--border-color);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(9, 9, 11, 0.8);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 700;
            font-size: 18px;
            letter-spacing: 0.05em;
            color: var(--text-main);
        }

        .logo span {
            color: var(--primary-text);
        }

        .logo-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: var(--primary);
            box-shadow: 0 0 10px var(--primary);
        }

        .tagline {
            font-size: 11px;
            color: var(--text-muted);
            letter-spacing: 0.1em;
            text-transform: uppercase;
            font-family: 'DM Mono', monospace;
            border: 1px solid var(--border-color);
            padding: 4px 12px;
            border-radius: 99px;
            background: rgba(24, 24, 27, 0.5);
        }

        /* Container Layout */
        main {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px 20px;
            position: relative;
        }

        .card-container {
            width: 100%;
            max-width: 650px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            position: relative;
            transition: all 0.3s ease;
        }

        .card-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--accent-blue));
        }

        .card-content {
            padding: 40px;
        }

        .step-section {
            display: none;
        }

        .step-section.active {
            display: block;
            animation: fadeIn 0.4s ease forwards;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h1 {
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--text-main) 30%, var(--text-muted) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .section-desc {
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 30px;
            line-height: 1.5;
        }

        /* Form Controls */
        .form-group {
            margin-bottom: 20px;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        label {
            display: block;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 8px;
            font-family: 'Outfit', sans-serif;
        }

        input, select, textarea {
            width: 100%;
            background-color: var(--bg-input);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            font-size: 14px;
            transition: all 0.2s ease;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }

        textarea {
            resize: vertical;
            min-height: 80px;
        }

        /* Buttons Style */
        .btn-row {
            display: flex;
            gap: 12px;
            margin-top: 30px;
        }

        .btn {
            flex: 1;
            padding: 14px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .btn-primary {
            background-color: var(--primary);
            border: 1px solid var(--primary);
            color: #FFFFFF;
        }

        .btn-primary:hover {
            background-color: #17855E;
            box-shadow: 0 0 15px rgba(29, 158, 117, 0.4);
        }

        .btn-secondary {
            background-color: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-main);
        }

        .btn-secondary:hover {
            border-color: var(--border-hover);
            background-color: var(--bg-input);
        }

        .btn-magic {
            background-color: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #93C5FD;
        }

        .btn-magic:hover {
            background-color: rgba(59, 130, 246, 0.2);
            border-color: rgba(59, 130, 246, 0.5);
        }

        /* Chat Console */
        .chat-console {
            border: 1px solid var(--border-color);
            background: #0E0E10;
            border-radius: 12px;
            height: 350px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            margin-bottom: 16px;
        }

        .chat-header {
            background-color: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-dot-green {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--primary-text);
            box-shadow: 0 0 8px var(--primary-text);
        }

        .chat-title {
            font-size: 11px;
            font-family: 'DM Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-muted);
        }

        .chat-messages {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .msg {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
            word-wrap: break-word;
        }

        .msg-agent {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }

        .msg-user {
            background-color: var(--primary);
            color: #FFFFFF;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .msg-info {
            background-color: rgba(59, 130, 246, 0.08);
            border: 1px solid rgba(59, 130, 246, 0.2);
            color: #93C5FD;
            align-self: center;
            max-width: 90%;
            font-size: 12px;
            border-radius: 6px;
            text-align: center;
            font-family: 'DM Mono', monospace;
            padding: 8px 14px;
        }

        .chat-input-row {
            padding: 12px;
            background-color: var(--bg-card);
            border-top: 1px solid var(--border-color);
            display: flex;
            gap: 8px;
        }

        .chat-input {
            flex: 1;
        }

        /* Loading Indicator Spinner */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 8px 12px;
            align-self: flex-start;
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 10px;
        }

        .dot {
            width: 6px;
            height: 6px;
            background-color: var(--text-muted);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }

        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
        }

        /* Final Scorecard */
        .scorecard-panel {
            background-color: #0E0E10;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }

        .score-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
        }

        .score-badge-main {
            font-size: 32px;
            font-weight: 800;
            color: var(--primary-text);
        }

        .status-badge {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            padding: 4px 12px;
            border-radius: 99px;
            border: 1px solid;
        }

        .status-badge.qualified {
            background-color: rgba(29, 158, 117, 0.1);
            border-color: rgba(29, 158, 117, 0.3);
            color: var(--primary-text);
        }

        .status-badge.nurture {
            background-color: rgba(245, 158, 11, 0.1);
            border-color: rgba(245, 158, 11, 0.3);
            color: var(--accent-orange);
        }

        .metric-bar-group {
            margin-bottom: 12px;
        }

        .metric-label-row {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        .progress-container {
            width: 100%;
            height: 6px;
            background-color: var(--bg-input);
            border-radius: 99px;
            overflow: hidden;
        }

        .progress-bar {
            height: 100%;
            border-radius: 99px;
        }

        .bg-emerald { background-color: var(--primary); }
        .bg-blue { background-color: var(--accent-blue); }
        .bg-orange { background-color: var(--accent-orange); }
        .bg-purple { background-color: #8B5CF6; }

        .enrichment-box {
            font-size: 13px;
            color: var(--text-muted);
            line-height: 1.5;
            background: var(--bg-card);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            margin-top: 16px;
        }
    </style>
</head>
<body>
    <div class="ambient-glow-1"></div>
    <div class="ambient-glow-2"></div>

    <header>
        <div class="logo">
            <div class="logo-dot"></div>
            PRESENCE<span>IX</span>
        </div>
        <div class="tagline">Lead Ingestion Simulator</div>
    </header>

    <main>
        <div class="card-container">
            <div class="card-content">
                <!-- STEP 1: SUBMISSION FORM -->
                <section id="step-form" class="step-section active">
                    <h1>Ingest Test Lead</h1>
                    <p class="section-desc">Simulate a buyer lead coming in from Zillow or Facebook to trigger the real-time AI Speed-To-Lead agent outreach.</p>
                    
                    <!-- Free Real-Time Alerts Status Bar -->
                    <div class="notification-status-bar" style="margin-bottom: 24px; padding: 14px 18px; border: 1px solid var(--border-color); border-radius: 8px; background: rgba(24, 24, 27, 0.4); display: flex; flex-direction: column; gap: 8px;">
                        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); font-family: 'DM Mono', monospace; display: flex; justify-content: space-between; align-items: center;">
                            <span>📱 Free Real-Time Alerts Status</span>
                            <span style="color: var(--primary-text); cursor: pointer; text-decoration: underline;" onclick="toggleAlertsGuide()">Help / Setup Guide ❓</span>
                        </div>
                        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                            <div id="status-telegram" style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-dark); background: rgba(0,0,0,0.1); padding: 4px 10px; border-radius: 4px; border: 1px solid var(--border-color); transition: all 0.3s;">
                                <div style="width: 8px; height: 8px; border-radius: 50%; background-color: var(--text-dark); transition: all 0.3s;" id="dot-telegram"></div>
                                Telegram Bot
                            </div>
                            <div id="status-slack" style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-dark); background: rgba(0,0,0,0.1); padding: 4px 10px; border-radius: 4px; border: 1px solid var(--border-color); transition: all 0.3s;">
                                <div style="width: 8px; height: 8px; border-radius: 50%; background-color: var(--text-dark); transition: all 0.3s;" id="dot-slack"></div>
                                Slack Webhook
                            </div>
                            <div id="status-whatsapp" style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-dark); background: rgba(0,0,0,0.1); padding: 4px 10px; border-radius: 4px; border: 1px solid var(--border-color); transition: all 0.3s;">
                                <div style="width: 8px; height: 8px; border-radius: 50%; background-color: var(--text-dark); transition: all 0.3s;" id="dot-whatsapp"></div>
                                WhatsApp API
                            </div>
                            <div style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--primary-text); background: rgba(29, 158, 117, 0.05); padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(29, 158, 117, 0.2);">
                                <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #1D9E75; box-shadow: 0 0 4px #1D9E75;"></div>
                                WhatsApp Forwarder (Active)
                            </div>
                        </div>
                        <div id="alerts-setup-guide" style="display: none; border-top: 1px solid var(--border-color); padding-top: 10px; margin-top: 4px; font-size: 12px; line-height: 1.5; color: var(--text-muted); text-align: left;">
                            <strong style="color: var(--text-main);">Quick Setup for Free Phone Notifications:</strong>
                            <ul style="margin-left: 16px; margin-top: 4px; display: flex; flex-direction: column; gap: 4px;">
                                <li><strong>Telegram:</strong> Search <span style="color: var(--text-main);">@BotFather</span>, create a bot for <code style="font-family: 'DM Mono', monospace; background: var(--bg-input); padding: 1px 4px; border-radius: 3px;">TELEGRAM_BOT_TOKEN</code>. Add bot and message <span style="color: var(--text-main);">@userinfobot</span> to get your <code style="font-family: 'DM Mono', monospace; background: var(--bg-input); padding: 1px 4px; border-radius: 3px;">TELEGRAM_CHAT_ID</code>.</li>
                                <li><strong>Slack:</strong> Enable Incoming Webhooks on any Slack App and use the URL as <code style="font-family: 'DM Mono', monospace; background: var(--bg-input); padding: 1px 4px; border-radius: 3px;">SLACK_WEBHOOK_URL</code>.</li>
                                <li><strong>WhatsApp API:</strong> Create a Meta App, configure WhatsApp Business (free tier 1k msgs/mo) to get <code style="font-family: 'DM Mono', monospace; background: var(--bg-input); padding: 1px 4px; border-radius: 3px;">WHATSAPP_ACCESS_TOKEN</code> and <code style="font-family: 'DM Mono', monospace; background: var(--bg-input); padding: 1px 4px; border-radius: 3px;">WHATSAPP_PHONE_NUMBER_ID</code>.</li>
                            </ul>
                        </div>
                    </div>

                    <form id="leadForm" onsubmit="submitLead(event)">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="name">Lead Full Name</label>
                                <input type="text" id="name" required placeholder="e.g. Sarah Connor">
                            </div>
                            <div class="form-group">
                                <label for="source">Lead Source</label>
                                <select id="source">
                                    <option value="Zillow Portal">Zillow Portal</option>
                                    <option value="Realtor.com">Realtor.com</option>
                                    <option value="Facebook Lead Ad">Facebook Lead Ad</option>
                                    <option value="PresenceIX Custom Widget">PresenceIX Custom Widget</option>
                                </select>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label for="email">Email Address</label>
                                <input type="email" id="email" required placeholder="e.g. s.connor@gmail.com">
                            </div>
                            <div class="form-group">
                                <label for="phone">Phone Number</label>
                                <input type="tel" id="phone" required placeholder="e.g. +1-555-0144">
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="notes">Simulated Search Criteria (Optional)</label>
                            <textarea id="notes" placeholder="e.g. Looking for a modern 3-bedroom luxury house near great schools, budget $800k. Needs to move fast!"></textarea>
                        </div>

                        <div class="btn-row">
                            <button type="button" class="btn btn-magic" onclick="magicFill()">🪄 Auto-Generate Buyer</button>
                            <button type="submit" class="btn btn-primary" id="submitBtn">Start AI Outreach ⚡</button>
                        </div>
                    </form>
                </section>

                <!-- STEP 2: CONVERSATION SIMULATOR -->
                <section id="step-chat" class="step-section">
                    <h1 id="chat-header-name">Interactive Agent Outreach</h1>
                    <p class="section-desc">Observe the AI's 60-second greeting, and chat back and forth to simulate a real SMS conversation. Type "exit" to score and sync to CRM.</p>

                    <div class="chat-console">
                        <div class="chat-header">
                            <div class="status-dot-green"></div>
                            <div class="chat-title">Live AI Concierge — Chat Simulator</div>
                        </div>
                        <div class="chat-messages" id="chat-messages">
                            <!-- Messages inserted dynamically -->
                        </div>
                        <!-- Typing loader indicator -->
                        <div class="typing-indicator" id="typing-loader" style="display: none;">
                            <div class="dot"></div>
                            <div class="dot"></div>
                            <div class="dot"></div>
                        </div>
                    </div>

                    <div class="chat-input-row">
                        <input type="text" class="chat-input" id="chat-reply-input" placeholder="Type simulated reply (or 'exit' to score & sync)..." onkeypress="handleChatKeypress(event)">
                        <button class="btn btn-primary" style="flex: 0; padding: 12px 24px;" onclick="sendChatMessage()">Send SMS</button>
                    </div>

                    <div class="btn-row">
                        <button class="btn btn-secondary" onclick="resetForm()">Reset Form</button>
                        <button class="btn btn-primary" style="background-color: var(--accent-orange); border-color: var(--accent-orange);" onclick="finishAndScoreLead()">Stop & Score Lead ⭐</button>
                    </div>
                </section>

                <!-- STEP 3: SCORECARD REVEAL -->
                <section id="step-scorecard" class="step-section">
                    <h1 id="score-lead-name">Jane Smith</h1>
                    <p class="section-desc">The AI analyzed the text dialogue log, calculated the qualification rubric score, and synchronized the lead instantly to your cloud backend.</p>

                    <div class="scorecard-panel">
                        <div class="score-header">
                            <div>
                                <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; font-family: 'DM Mono', monospace;">Agent Scorecard</div>
                                <div class="score-badge-main" id="overall-score-badge">⭐ 8.8/10</div>
                            </div>
                            <div class="status-badge qualified" id="status-badge">QUALIFIED</div>
                        </div>

                        <div class="metric-bar-group">
                            <div class="metric-label-row">
                                <span>Budget Rubric</span>
                                <span id="metric-val-budget">8.5 / 10.0</span>
                            </div>
                            <div class="progress-container">
                                <div class="progress-bar bg-emerald" id="bar-budget" style="width: 85%;"></div>
                            </div>
                        </div>

                        <div class="metric-bar-group">
                            <div class="metric-label-row">
                                <span>Timeline Rubric</span>
                                <span id="metric-val-timeline">9.0 / 10.0</span>
                            </div>
                            <div class="progress-container">
                                <div class="progress-bar bg-blue" id="bar-timeline" style="width: 90%;"></div>
                            </div>
                        </div>

                        <div class="metric-bar-group">
                            <div class="metric-label-row">
                                <span>Motivation Rubric</span>
                                <span id="metric-val-motivation">8.0 / 10.0</span>
                            </div>
                            <div class="progress-container">
                                <div class="progress-bar bg-orange" id="bar-motivation" style="width: 80%;"></div>
                            </div>
                        </div>

                        <div class="metric-bar-group">
                            <div class="metric-label-row">
                                <span>Agent Representation</span>
                                <span id="metric-val-representation">10.0 / 10.0</span>
                            </div>
                            <div class="progress-container">
                                <div class="progress-bar bg-purple" id="bar-representation" style="width: 100%;"></div>
                            </div>
                        </div>

                        <div class="enrichment-box" id="enrichment-content">
                            <!-- Enrichment loaded dynamically -->
                        </div>
                    </div>

                    <div class="btn-row">
                        <button class="btn btn-secondary" onclick="resetForm()">Ingest Another Lead</button>
                        <a href="https://studio.softr.io/dashboard" target="_blank" class="btn btn-primary">Open Live Softr Dashboard 🚀</a>
                    </div>
                </section>
            </div>
        </div>
    </main>

    <script>
        let currentLeadId = "";
        let leadInfo = {};

        // Free real-time alert connections checker
        async function fetchNotificationStatus() {
            try {
                const response = await fetch("/api/notification-status");
                if (!response.ok) return;
                const status = await response.json();
                
                if (status.telegram) {
                    const dot = document.getElementById("dot-telegram");
                    if (dot) {
                        dot.style.backgroundColor = "var(--primary)";
                        dot.style.boxShadow = "0 0 8px var(--primary)";
                        document.getElementById("status-telegram").style.color = "var(--text-main)";
                        document.getElementById("status-telegram").style.borderColor = "rgba(29, 158, 117, 0.3)";
                        document.getElementById("status-telegram").style.background = "rgba(29, 158, 117, 0.05)";
                    }
                }
                if (status.slack) {
                    const dot = document.getElementById("dot-slack");
                    if (dot) {
                        dot.style.backgroundColor = "var(--primary)";
                        dot.style.boxShadow = "0 0 8px var(--primary)";
                        document.getElementById("status-slack").style.color = "var(--text-main)";
                        document.getElementById("status-slack").style.borderColor = "rgba(29, 158, 117, 0.3)";
                        document.getElementById("status-slack").style.background = "rgba(29, 158, 117, 0.05)";
                    }
                }
                if (status.whatsapp) {
                    const dot = document.getElementById("dot-whatsapp");
                    if (dot) {
                        dot.style.backgroundColor = "var(--primary)";
                        dot.style.boxShadow = "0 0 8px var(--primary)";
                        document.getElementById("status-whatsapp").style.color = "var(--text-main)";
                        document.getElementById("status-whatsapp").style.borderColor = "rgba(29, 158, 117, 0.3)";
                        document.getElementById("status-whatsapp").style.background = "rgba(29, 158, 117, 0.05)";
                    }
                }
            } catch (err) {
                console.error("Failed to fetch notification status:", err);
            }
        }

        function toggleAlertsGuide() {
            const guide = document.getElementById("alerts-setup-guide");
            if (guide) {
                guide.style.display = guide.style.display === "none" ? "block" : "none";
            }
        }

        window.addEventListener("DOMContentLoaded", () => {
            fetchNotificationStatus();
        });

        // Premium Buyer Generation profiles
        const mockBuyers = [
            {
                name: "Charlotte Vanderbilt",
                email: "c.vanderbilt@vanderbilt-holdings.com",
                phone: "+1-212-555-0199",
                source: "Zillow Portal",
                notes: "Looking for an exclusive luxury estate in Beverly Hills. Budget is flexible up to $4.5M. Ready to buy in cash, completely unrepresented."
            },
            {
                name: "Marcus Aurelius",
                email: "marcus.aurelius@stoicadvisory.com",
                phone: "+1-415-555-0812",
                source: "Realtor.com",
                notes: "Relocating from San Francisco to Austin next month. Needs a 4-bedroom house with study, fast fiber optic internet, budget $1.2M. Already pre-approved."
            },
            {
                name: "Devon Carter",
                email: "devon.carter@techventures.io",
                phone: "+1-305-555-0143",
                source: "Facebook Lead Ad",
                notes: "Interested in new waterfront development properties in Miami. Budget around $900k. Just browsing, but motivated if the right deal comes up."
            }
        ];

        function magicFill() {
            const randomIndex = Math.floor(Math.random() * mockBuyers.length);
            const buyer = mockBuyers[randomIndex];
            
            document.getElementById("name").value = buyer.name;
            document.getElementById("email").value = buyer.email;
            document.getElementById("phone").value = buyer.phone;
            document.getElementById("source").value = buyer.source;
            document.getElementById("notes").value = buyer.notes;

            // Simple micro-animation on fill
            const inputs = ["name", "email", "phone", "source", "notes"];
            inputs.forEach(id => {
                const el = document.getElementById(id);
                el.style.borderColor = "var(--primary)";
                setTimeout(() => el.style.borderColor = "var(--border-color)", 600);
            });
        }

        async function submitLead(event) {
            event.preventDefault();
            
            const submitBtn = document.getElementById("submitBtn");
            submitBtn.innerHTML = "Enriching & Ingesting...";
            submitBtn.disabled = true;

            leadInfo = {
                name: document.getElementById("name").value,
                phone: document.getElementById("phone").value,
                email: document.getElementById("email").value,
                source: document.getElementById("source").value,
                notes: document.getElementById("notes").value
            };

            try {
                const response = await fetch("/api/submit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(leadInfo)
                });

                if (!response.ok) throw new Error("Failed to ingest lead");
                
                const data = await response.json();
                currentLeadId = data.lead_id;

                // Move to Chat Step
                document.getElementById("chat-header-name").innerText = `Outreach for ${leadInfo.name}`;
                document.getElementById("step-form").classList.remove("active");
                document.getElementById("step-chat").classList.add("active");

                // Populate chat with initial outreach
                const chatBox = document.getElementById("chat-messages");
                const cleanPhone = leadInfo.phone ? leadInfo.phone.replace(/[^0-9]/g, '') : '';
                const encodedText = encodeURIComponent(data.outreach_message);
                const waUrl = `https://wa.me/${cleanPhone}?text=${encodedText}`;
                
                chatBox.innerHTML = `
                    <div class="msg msg-info">System: New lead ingested. Enriched data compiled and synced to Airtable as IN_PROGRESS.</div>
                    <div class="msg msg-agent">
                        ${data.outreach_message}
                        <div style="margin-top: 6px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.05); font-size: 11px; display: flex; justify-content: flex-end;">
                            <a href="${waUrl}" target="_blank" style="color: #25D366; text-decoration: none; font-weight: 500; display: inline-flex; align-items: center; gap: 4px; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style="display: block;"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946C.06 5.348 5.397.01 12.008.01c3.202.001 6.212 1.246 8.477 3.514 2.266 2.268 3.507 5.28 3.505 8.484-.004 6.657-5.34 11.997-11.953 11.997-2.005-.001-3.973-.502-5.753-1.454L0 24zm6.59-4.846c1.6.95 3.188 1.449 4.825 1.451 5.436 0 9.86-4.37 9.863-9.755.002-2.61-1.01-5.063-2.853-6.918C16.638 2.077 14.19 1.06 11.605 1.06 6.168 1.06 1.745 5.43 1.741 10.817c-.001 1.648.504 3.257 1.464 4.877L2.24 21.053l4.407-1.899zm11.534-5.642c-.303-.152-1.797-.887-2.075-.988-.278-.102-.48-.152-.683.151-.202.304-.783.988-.96 1.19-.177.203-.354.228-.658.076-.303-.152-1.28-.472-2.438-1.504-.901-.804-1.51-1.797-1.687-2.1-.177-.304-.019-.468.133-.619.136-.136.303-.354.455-.531.152-.177.202-.304.303-.506.102-.203.051-.38-.025-.531-.076-.151-.683-1.648-.936-2.28-.246-.615-.497-.531-.683-.531-.177 0-.38-.025-.582-.025-.203 0-.531.076-.81.431-.278.354-1.063 1.039-1.063 2.533 0 1.493 1.088 2.937 1.24 3.139.152.203 2.14 3.268 5.182 4.582.723.314 1.288.502 1.728.643.727.23 1.388.198 1.91.134.582-.072 1.798-.734 2.05-1.442.253-.709.253-1.316.177-1.442-.076-.127-.278-.203-.582-.355z"/></svg>
                                Forward on WhatsApp
                            </a>
                        </div>
                    </div>
                `;
            } catch (err) {
                alert("Error submitting lead: " + err.message);
            } finally {
                submitBtn.innerHTML = "Start AI Outreach ⚡";
                submitBtn.disabled = false;
            }
        }

        async function sendChatMessage() {
            const inputEl = document.getElementById("chat-reply-input");
            const text = inputEl.value.trim();
            if (!text) return;

            inputEl.value = "";
            appendMessage(text, "user");

            if (text.toLowerCase() === "exit" || text.toLowerCase() === "quit") {
                finishAndScoreLead();
                return;
            }

            // Show typing indicator
            const loader = document.getElementById("typing-loader");
            loader.style.display = "flex";
            scrollToBottom();

            try {
                const response = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        lead_id: currentLeadId,
                        message: text
                    })
                });

                if (!response.ok) throw new Error("Connection failed");

                const data = await response.json();
                
                // Hide loader
                loader.style.display = "none";
                
                // Append AI response
                appendMessage(data.reply, "agent");
            } catch (err) {
                loader.style.display = "none";
                appendMessage("⚠️ Error communicating with AI: " + err.message, "info");
            }
        }

        function handleChatKeypress(event) {
            if (event.key === "Enter") {
                sendChatMessage();
            }
        }

        function appendMessage(text, role) {
            const chatBox = document.getElementById("chat-messages");
            const msgClass = role === "user" ? "msg-user" : (role === "agent" ? "msg-agent" : "msg-info");
            
            let html = `<div class="msg ${msgClass}">${text}`;
            if (role === "agent") {
                const cleanPhone = leadInfo && leadInfo.phone ? leadInfo.phone.replace(/[^0-9]/g, '') : '';
                const encodedText = encodeURIComponent(text);
                const waUrl = `https://wa.me/${cleanPhone}?text=${encodedText}`;
                html += `
                    <div style="margin-top: 6px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.05); font-size: 11px; display: flex; justify-content: flex-end;">
                        <a href="${waUrl}" target="_blank" style="color: #25D366; text-decoration: none; font-weight: 500; display: inline-flex; align-items: center; gap: 4px; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style="display: block;"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946C.06 5.348 5.397.01 12.008.01c3.202.001 6.212 1.246 8.477 3.514 2.266 2.268 3.507 5.28 3.505 8.484-.004 6.657-5.34 11.997-11.953 11.997-2.005-.001-3.973-.502-5.753-1.454L0 24zm6.59-4.846c1.6.95 3.188 1.449 4.825 1.451 5.436 0 9.86-4.37 9.863-9.755.002-2.61-1.01-5.063-2.853-6.918C16.638 2.077 14.19 1.06 11.605 1.06 6.168 1.06 1.745 5.43 1.741 10.817c-.001 1.648.504 3.257 1.464 4.877L2.24 21.053l4.407-1.899zm11.534-5.642c-.303-.152-1.797-.887-2.075-.988-.278-.102-.48-.152-.683.151-.202.304-.783.988-.96 1.19-.177.203-.354.228-.658.076-.303-.152-1.28-.472-2.438-1.504-.901-.804-1.51-1.797-1.687-2.1-.177-.304-.019-.468.133-.619.136-.136.303-.354.455-.531.152-.177.202-.304.303-.506.102-.203.051-.38-.025-.531-.076-.151-.683-1.648-.936-2.28-.246-.615-.497-.531-.683-.531-.177 0-.38-.025-.582-.025-.203 0-.531.076-.81.431-.278.354-1.063 1.039-1.063 2.533 0 1.493 1.088 2.937 1.24 3.139.152.203 2.14 3.268 5.182 4.582.723.314 1.288.502 1.728.643.727.23 1.388.198 1.91.134.582-.072 1.798-.734 2.05-1.442.253-.709.253-1.316.177-1.442-.076-.127-.278-.203-.582-.355z"/></svg>
                            Forward on WhatsApp
                        </a>
                    </div>`;
            }
            html += `</div>`;
            chatBox.innerHTML += html;
            scrollToBottom();
        }

        function scrollToBottom() {
            const chatBox = document.getElementById("chat-messages");
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function finishAndScoreLead() {
            // Loader
            appendMessage("⚖️ Triggering Lead Scorer Swarm and compiling final qualification profiles...", "info");
            scrollToBottom();

            try {
                const response = await fetch(`/api/score/${currentLeadId}`);
                if (!response.ok) throw new Error("Failed to score lead");
                
                const data = await response.json();

                // Load Scorecard View
                document.getElementById("score-lead-name").innerText = leadInfo.name;
                document.getElementById("overall-score-badge").innerText = `⭐ ${data.final_score.toFixed(1)}/10`;
                
                // Set Status Badge
                const statusBadge = document.getElementById("status-badge");
                statusBadge.innerText = data.status.toUpperCase();
                if (data.status.toUpperCase() === "QUALIFIED") {
                    statusBadge.className = "status-badge qualified";
                } else {
                    statusBadge.className = "status-badge nurture";
                }

                // Map Progress Bars
                const scores = data.scores || {};
                const budget = scores.budget || 5.0;
                const timeline = scores.timeline || 5.0;
                const motivation = scores.motivation || 5.0;
                const representation = scores.representation || 5.0;

                document.getElementById("metric-val-budget").innerText = `${budget.toFixed(1)} / 10.0`;
                document.getElementById("bar-budget").style.width = `${budget * 10}%`;

                document.getElementById("metric-val-timeline").innerText = `${timeline.toFixed(1)} / 10.0`;
                document.getElementById("bar-timeline").style.width = `${timeline * 10}%`;

                document.getElementById("metric-val-motivation").innerText = `${motivation.toFixed(1)} / 10.0`;
                document.getElementById("bar-motivation").style.width = `${motivation * 10}%`;

                document.getElementById("metric-val-motivation").style.width = `${motivation * 10}%`;

                document.getElementById("metric-val-representation").innerText = `${representation.toFixed(1)} / 10.0`;
                document.getElementById("bar-representation").style.width = `${representation * 10}%`;

                // Set Enrichment info
                document.getElementById("enrichment-content").innerHTML = `
                    <div style="font-weight:700; margin-bottom: 8px; color: var(--primary-text); font-family: 'DM Mono', monospace;">📂 Zillow & Contact Intelligence Data:</div>
                    ${data.enriched_info.replace(/\\n/g, "<br>")}
                `;

                // Slide panels
                document.getElementById("step-chat").classList.remove("active");
                document.getElementById("step-scorecard").classList.add("active");

            } catch (err) {
                alert("Error compiling scorecard: " + err.message);
            }
        }

        function resetForm() {
            document.getElementById("leadForm").reset();
            document.getElementById("step-chat").classList.remove("active");
            document.getElementById("step-scorecard").classList.remove("active");
            document.getElementById("step-form").classList.add("active");
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.get("/api/notification-status")
async def get_notification_status():
    """
    Checks if Free Real Notification channels are configured in .env
    """
    return {
        "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
        "slack": bool(os.getenv("SLACK_WEBHOOK_URL")),
        "whatsapp": bool(os.getenv("WHATSAPP_ACCESS_TOKEN") and os.getenv("WHATSAPP_PHONE_NUMBER_ID"))
    }


@app.post("/api/submit")
async def submit_lead(lead: LeadSubmission):
    lead_id = f"lead_{uuid.uuid4().hex[:8]}"
    lead_info = {
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "source": lead.source,
        "notes": lead.notes
    }
    
    try:
        # Run local agent initialization outreach (Enricher, Outreach, Sync to Airtable)
        outreach_msg = process_incoming_message(lead_id, lead_info)
        return {"lead_id": lead_id, "outreach_message": outreach_msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_lead(msg: ChatMessage):
    # Retrieve current profile data from State first to satisfy requirements
    sqlite_state = get_lead_state_from_sqlite(msg.lead_id)
    if not sqlite_state:
        raise HTTPException(status_code=404, detail="Lead session not found.")
        
    lead_info = {
        "name": sqlite_state.get("name", "there"),
        "phone": sqlite_state.get("phone", ""),
        "email": sqlite_state.get("email", ""),
        "source": sqlite_state.get("source", "Zillow")
    }
    
    try:
        # Trigger interactive reply (Qualifier)
        ai_reply = process_incoming_message(msg.lead_id, lead_info, user_reply=msg.message)
        return {"reply": ai_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/score/{lead_id}")
async def score_lead(lead_id: str):
    # Force full qualification execution: Load state and send "exit" to score & sync
    sqlite_state = get_lead_state_from_sqlite(lead_id)
    if not sqlite_state:
        raise HTTPException(status_code=404, detail="Lead session not found.")
        
    lead_info = {
        "name": sqlite_state.get("name", "there"),
        "phone": sqlite_state.get("phone", ""),
        "email": sqlite_state.get("email", ""),
        "source": sqlite_state.get("source", "Zillow")
    }
    
    try:
        # Send "exit" which breaks the SMS loop, triggers scorer and writes to Airtable
        process_incoming_message(lead_id, lead_info, user_reply="exit")
        
        # Load the updated scored state
        scored_state = get_lead_state_from_sqlite(lead_id)
        
        return {
            "name": scored_state.get("name", "there"),
            "enriched_info": scored_state.get("enriched_info", "Enrichment complete."),
            "scores": scored_state.get("scores", {}),
            "final_score": scored_state.get("final_score", 1.0),
            "status": scored_state.get("status", "QUALIFIED")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("      🚀 INITIATING PRESENCEIX LEAD INGESTION WEB PORTAL 🚀")
    print("=" * 65)
    print(" Starting development server inside local python venv...")
    print(" You can open your browser to run interactive tests:")
    print("\n      👉  http://localhost:8000  👈\n")
    print(" Clicking this link will allow you to:")
    print("  1. Ingest test leads into Zillow/Facebook mockup forms.")
    print("  2. Simulate live 2-way SMS chat with the real estate AI concierge.")
    print("  3. View real-time qualification scores (motivation, budget, etc.).")
    print("  4. See updates sync in real-time to your Airtable base and Softr CRM!")
    print("=" * 65 + "\n")
    
    # Automatically open local browser window
    try:
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass
        
    uvicorn.run(app, host="127.0.0.1", port=8000, uvicorn_log_level="info")
