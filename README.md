# LangGraph Multi-Agent Swarm (PresenceIX Orchestration Layer)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/framework-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Claude 3.5](https://img.shields.io/badge/brain-Claude_3.5_Sonnet-purple.svg)](https://anthropic.com)
[![Airtable Sync](https://img.shields.io/badge/CRM-Airtable_Sync-blue.svg)](https://airtable.com)

Welcome to the **PresenceIX Multi-Agent Swarm Orchestrator**, a graduate-level AI backend implementing state-of-the-art agentic patterns. Built using **LangGraph** and **Anthropic Claude 3.5 (Sonnet & Haiku)**, this system orchestrates specialized, state-persisted multi-agent swarms designed to automate real-world operations for high-growth businesses and enterprise pipelines.

This is the production-grade core engine behind **PresenceIX**—an AI Automation Agency (AAA) founded by Kachi Ezibe, which builds autonomous workflows that eliminate manual work, automate CRM records, and qualify outbound leads in real-time.

---

## 📐 1. System Architecture

The orchestrator operates two core, independent agent swarms running on a unified state management layer with full SQLite-backed checkpointing.

```mermaid
graph TD
    %% Swarm A: Content Brain
    subgraph Swarm A: Content Brain (Parallel Fork-Join)
        Topic[Input: Trend/Topic] --> Researcher[Researcher Node: Trend Discovery]
        Researcher --> |Parallel Fork| LinkedIn[LinkedIn Writer Node]
        Researcher --> |Parallel Fork| XThread[X Thread Writer Node]
        Researcher --> |Parallel Fork| VideoScript[Video Scriptwriter Node]
        LinkedIn --> |Join| Exporter[Exporter Node: Save & Compile]
        XThread --> |Join| Exporter
        VideoScript --> |Join| Exporter
        Exporter --> AirtableCalendar[(Airtable Content Calendar)]
    end

    %% Swarm B: Speed-to-Lead
    subgraph Swarm B: Speed-to-Lead (Conditional State Machine)
        LeadIn[Ingest: Lead Profile] --> Orchestrator[Orchestrator Router]
        Orchestrator --> |Route Condition| Route{Has History?}
        Route --> |No: First Touch| Enricher[Enricher Node: Hunter.io + Zillow Profile]
        Enricher --> Outreach[Outreach Node: 60s Conversational SMS]
        Outreach --> Sync[(Airtable CRM & Local Backup)]
        
        Route --> |Yes: User Replied| Qualifier[Qualifier Node: gentle probing]
        Qualifier --> Scorer[Scorer Node: Multi-Dimensional Evaluator]
        Scorer --> Sync
    end
    
    style Exporter fill:#d4edda,stroke:#28a745,stroke-width:2px
    style Sync fill:#cce5ff,stroke:#004085,stroke-width:2px
    style Route fill:#fff3cd,stroke:#856404,stroke-width:2px
```

### 🧠 Swarm A: The Content Brain (7-Day Planner)
Implements a highly efficient **parallel fork-join** execution pattern to generate omni-channel marketing calendars from a single topic:
1. **Researcher Node:** Gathers industry facts, pain points, and eye-opening statistics using Claude 3.5 Haiku.
2. **Parallel Copywriters:** Forks the research notes to three specialized Claude 3.5 Sonnet writing nodes simultaneously:
   - **LinkedIn Writer:** Focuses on professional spacing, storytelling, and high-value hooks.
   - **X Thread Writer:** Ghostwrites highly viral, 4-6 tweet educational threads structured with character-limit validation.
   - **Video Scriptwriter:** Visualizes and drafts vertical video scripts (TikTok/Reels) with video-cue tables and retention hooks.
3. **Exporter Node:** Joins the parallel threads, compiles the structured drafts, saves a local JSON backup, and pushes the payload directly to a live Airtable Content Calendar base.

### 🎯 Swarm B: Speed-to-Lead (Real Estate Ingestion & Concierge)
Implements an interactive **conversational state graph** featuring automated enrichment, B2B verification, and multi-dimensional lead scoring:
1. **Orchestrator Router:** Evaluates incoming webhooks or SMS events to decide between *First-Touch Ingestion* or *Ongoing Dialogue*.
2. **Lead Enricher Node:** Interfaces with **Hunter.io via Composio** to verify B2B email deliverability and confidence, and merges local real estate data to create rich buyer profiles.
3. **Outreach Node:** Drafts and dispatches a warm, personalized 60-second greeting SMS containing local neighborhood references and a low-friction question.
4. **Qualifier Node:** Analyzes client replies to probe gently for missing qualifying data (Budget, Timeline, Motivation, Representation) without sounding like a form questionnaire.
5. **Scorer Node:** Evaluates the full chat transcript against a strict business rubric, compiling individual sub-scores out of 10.0 and updating the status (QUALIFIED, NURTURE, DISQUALIFIED).
6. **Sync Node:** Bi-directionally syncs state updates to the Airtable CRM Leads Base and SQLite checkpoint tables.

---

## 🔌 2. Advanced Integrations

- **Unified LLM Router (`llm_router.py`):** Features a flexible LLM connection broker supporting seven major API providers (Anthropic, OpenAI, Groq, DeepSeek, Mistral, Google Gemini, OpenRouter) with automatic API key-detection and graceful model fallback trees.
- **Bi-directional CRM Synchronization (`airtable_sync.py`):** Supports OAuth-based **Composio** triggers as well as standard Direct HTTP REST integrations with Airtable, ensuring lead records and content calendars sync in less than 3 seconds.
- **Asynchronous Notifications (`notifications.py`):** Connects to Twilio, Telegram, and Slack webhooks to notify business administrators instantly when a new lead is ingested or when a client is classified as "QUALIFIED" with their full CRM scorecard.
- **SQLite Conversational Checkpointing (`main.py`):** Uses LangGraph's `SqliteSaver` checkpointer to serialize and preserve conversational memory graphs across arbitrary execution boundaries, ensuring the AI agent never loses chat context.

---

## 💻 3. Repository File Guide

```
├── main.py                     # Main CLI Entry Point & Interactive Chat Simulator
├── llm_router.py               # Provider-Agnostic LLM Routing Broker
├── agent_content_brain.py      # Swarm A: Parallel Fork-Join Marketing Engine
├── agent_speed_to_lead.py      # Swarm B: Conditional State Machine SMS Concierge
├── airtable_sync.py            # Airtable REST & Composio OAuth Sync Connector
├── notifications.py            # Twilio SMS, Telegram, and Slack Dispatcher
├── requirements.txt            # Python Dependencies
├── .gitignore                  # Production Git Ignore (Blocks secrets, DBs, and logs)
│
├── discover_airtable_base.py   # Utility: Auto-discovers table schemas and IDs
├── link_telegram.py            # Utility: Sets up Telegram webhook polling
├── list_all_connections.py     # Utility: Lists connected SaaS accounts in Composio
│
└── [Tests/]                    # Comprehensive Unit & Integration Tests
    ├── test_ai.py              # Tests LLM connection and chat response
    ├── test_airtable_sync.py   # Simulates Airtable record patch operations
    ├── test_composio.py        # Verifies Hunter.io and Composio token authorization
    ├── test_models.py          # Benchmarks model formatting and system prompts
    ├── test_notifications.py   # Tests webhook dispatcher connectivity
    ├── test_speed_to_lead_enricher.py # Tests simulated Zillow and scraper lookups
    └── test_tool_execution.py  # Tests isolated node state modifications
```

---

## 🚀 4. Local Installation & Live Simulation

### Prerequisites
- Python 3.10 or higher
- An active API key from OpenAI, Anthropic, or Groq (placed in `.env`)

### Step 1: Clone and Set Up Environment
```bash
# Clone the repository
git clone https://github.com/kachiezibe/langgraph-agent-swarm.git
cd langgraph-agent-swarm

# Initialize virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` (or create `.env`) in the root directory:
```env
LLM_PROVIDER="openai"             # Options: anthropic, openai, groq, deepseek, gemini
LLM_MODEL="gpt-4o-mini"           # Options: claude-3-5-sonnet, gpt-4o-mini, llama-3.1-8b-instant

# API Credentials (Fill in the ones you use; others will use mock simulations)
OPENAI_API_KEY="your_openai_api_key"
ANTHROPIC_API_KEY="your_anthropic_api_key"
GROQ_API_KEY="your_groq_api_key"

# CRM & Notifications (Optional)
AIRTABLE_PERSONAL_ACCESS_TOKEN="pat_your_token"
AIRTABLE_BASE_ID="app_your_base_id"
TELEGRAM_BOT_TOKEN="bot_token"
TELEGRAM_ADMIN_CHAT_ID="chat_id"
```

### Step 3: Launch the Autonomous Swarm Simulators
Run the main orchestrator CLI to enter the interactive client simulation consoles:
```bash
python main.py
```

- **Choose Option 1** to simulate a live real estate lead ingestion. You can chat as a prospective homebuyer (e.g. Jane Smith or a custom lead) and watch the agent dynamically reply, probe, score, and sync your record in real-time.
- To run Swarm A independently, run:
```bash
python agent_content_brain.py
```

---

## 🏅 5. Academic & Admissions Context
This project serves as a key practical showcase in Kachi Ezibe’s application portfolio for **Fall 2027 Computer Science & AI Admissions** in the USA and Canada. 

It highlights:
- **Advanced State Graph Design:** Mastery of cyclic graph architectures, parallel execution, and join-node compilation.
- **Production-Grade Engineering:** Moving beyond simple LLM wrapping by implementing strict validation rubrics, SQLite checkpoints, and secure SaaS credential connectors.
- **Entrepreneurial Initiative:** Practical execution of multi-agent engineering to deliver measurable, automated revenue operations for local small businesses.