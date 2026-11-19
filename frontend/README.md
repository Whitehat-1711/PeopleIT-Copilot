# 💻 WorkPulse AI — Streamlit Frontend Interface

The frontend for **WorkPulse AI** is a polished, enterprise-grade dark-themed web chat application built using **Streamlit (v1.40+)**. It connects directly to the FastAPI backend service over Server-Sent Events (SSE) and REST APIs.

---

## 🎨 Design System & Theme

The user interface adheres to a modern, dark-mode design system tailored for high legibility, crisp contrast, and enterprise polish:

| Element | Color Hex / Style | Purpose |
| :--- | :--- | :--- |
| **Viewport Background** | `#0F172A` (Slate 900) | Deep dark background reducing eye strain |
| **Sidebar Background** | `#0B0F19` (Slate 950) | Distinct sidebar boundary with `#1E293B` divider |
| **Card / Bubble Background**| `#1E293B` (Slate 800) | Clean container elevation with `#334155` border |
| **Primary Typography** | `#F8FAFC` (Slate 50) | Bright off-white for 100% legibility |
| **Secondary Typography** | `#94A3B8` (Slate 400) | Crisp muted gray for labels and metadata |
| **Brand Accent** | `#818CF8` &rarr; `#C084FC` | Gradient indigo accent for the "AI" brand tag |
| **Pinned Input Bar** | Root `st.chat_input` | Fixed to bottom viewport with sticky container |

Theme tokens are defined in `.streamlit/config.toml`:

```toml
[theme]
base = "dark"
primaryColor = "#6366F1"
backgroundColor = "#0F172A"
secondaryBackgroundColor = "#1E293B"
textColor = "#F8FAFC"
font = "sans serif"

[server]
headless = true
```

---

## 🧭 Navigation & Layout Structure

The application layout is divided into two primary sections:

### 1. Left Sidebar
- **Brand Header**: `💼 WorkPulse AI` logo with tagline and active backend health probe.
- **SSO Identity Switcher (Task E5)**:
  - Dropdown populated dynamically from `GET /employees` across all 12 directory employees.
  - Selecting an employee immediately starts a brand-new session (`thread_id`), ensuring **zero cross-employee memory leakage**.
  - Demo banner: *"Demo Mode Active: Switch identity to test Row-Level Security isolation. In production, identity is verified via corporate SSO."*
- **New Chat Button**: Instantly resets the session and clears conversation history.
- **Suggested Questions (Demo Script)**: One-click scenario buttons (Leave Balance, Carryover Follow-up, VPN Setup, Injection Test) that trigger scripted queries into the main chat window.

### 2. Main Area (Tabbed Navigation)
The main pane is organized into three tabs:

```
[💬 Assistant Chat]    [📊 Audit Log & Analytics]    [📜 Policy Handbook]
```

#### Tab 1: 💬 Assistant Chat
- **Pinned Bottom Chat Input**: The input bar is placed at root level, ensuring it remains fixed at the bottom of the viewport at all times.
- **Streaming Tokens**: Assistant responses stream token-by-token using an SSE consumer (`POST /chat/stream`).
- **Route Badges**: Distinct badges visually indicate how the query was handled:
  - `📚 Policy Lookup` (RAG)
  - `💾 Employee Record` (PostgreSQL RLS)
  - `⚡ Hybrid Policy & Data`
  - `🎫 Escalation Ticket`
  - `🚫 Guardrail Blocked`
  - `💬 Direct Response`
- **Source Chips**: Interactive chips displaying exact document references: `📄 hr_policy.md › Annual Leave`.
- **How I Answered (Accordion)**: Expandable transparency panel displaying the execution route, confidence score, audit turn ID, and retrieved text snippets.
- **Support Ticket Cards**: Displayed with ticket ID and department contact when unanswerable questions escalate.
- **User Feedback**: Inline thumbs up (`👍 Helpful`) and thumbs down (`👎 Not helpful`) buttons linked to the PostgreSQL `feedback` table.

#### Tab 2: 📊 Audit Log & Analytics
- Live dashboard fetching recent rows from `GET /audit?limit=50`.
- Summary metrics: Total Intercepted Turns, Security Guardrails Blocked, Average Turn Latency (ms), and Escalation Tickets.
- Interactive data table showing turn IDs, timestamps, employees, PII-redacted queries, route names, and guardrail flags.

#### Tab 3: 📜 Policy Handbook
- Knowledge base explorer allowing users to inspect the indexed markdown policies (`hr_policy.md`, `it_policy.md`, `expenses_travel_policy.md`, etc.).

---

## 🚀 Running the Streamlit App

### Prerequisites
Make sure the FastAPI backend server is running on port **8001**:
```powershell
.\run.ps1 api
```

### Launch Streamlit
```powershell
# Using the PowerShell helper:
.\run.ps1 ui

# Or directly with the Streamlit CLI:
streamlit run frontend/app.py --server.port 8501
```

Open your browser to: [http://localhost:8501](http://localhost:8501)
