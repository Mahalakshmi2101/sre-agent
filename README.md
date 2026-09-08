# 🛡️ SRE Agent — Enterprise Cloud Incident Triage System

> Built for HiDevs AI Quest: Beyond the Wrapper | PS-03 | Solo Submission

A production-grade governed multi-agent SRE system that autonomously triages cloud incidents, diagnoses root causes using LLM reasoning, and executes safe remediations — with human approval gates for destructive actions.
🌐 **Live Demo:** https://sre-agent-iuva.onrender.com/dashboard  
📡 **API Docs:** https://sre-agent-iuva.onrender.com/docs  
🔗 **GitHub:** https://github.com/Mahalakshmi2101/sre-agent


---

## 🏗️ Architecture
Alert Ingestion → Triage Agent → AI Diagnostic Agent → Remediation Agent → Post-Mortem
↓
HITL Safety Gate
(blocks DELETE/DROP/REBOOT)

## 🤖 Agent Pipeline

| Agent | Role | Key Feature |
|---|---|---|
| **Triage Agent** | Groups noisy alerts by service, classifies P0-P4 severity | Auto-escalates to P0 if service fires 3+ times |
| **AI Diagnostic Agent** | LLM-powered root cause analysis from logs | Uses Groq inference — HIGH confidence output |
| **Remediation Agent** | Executes safe fixes, blocks dangerous ones | HITL gate stops DELETE/DROP/REBOOT/RESTART/KILL |

## 🔒 Safety Features

- **HITL Gate:** Destructive infrastructure commands are blocked and require explicit human approval before execution
- **AIMS Audit Log:** Every agent decision logged with timestamp, service, action, and status
- **P0 Escalation:** Services with 3+ historical alerts automatically escalated to P0
- **Confidence Scoring:** LOW confidence diagnoses flagged separately for human review

## 🚀 Live Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | System info |
| `/health` | GET | Agent health status |
| `/triage` | GET | Run triage agent only |
| `/analyze` | GET | Full pipeline — all 3 agents |
| `/analyze/custom` | POST | Inject custom alerts |
| `/history` | GET | Incident run history |
| `/dashboard` | GET | Real-time incident UI |
| `/docs` | GET | Auto-generated API docs |

## 🧪 Custom Alert Injection

```bash
curl -X POST "https://sre-agent-iuva.onrender.com/analyze/custom" \
  -H "Content-Type: application/json" \
  -d '{"alerts": [{"service": "payment-api", "message": "CPU spike 98%", "type": "cpu_spike", "severity": "P1"}]}'
```

## 📊 Evaluation Rubric Coverage

| Rubric Pillar | Implementation |
|---|---|
| Lyzr Agent Orchestration (30%) | 3-agent pipeline with clear task separation, tool calling, state persistence via SERVICE_HISTORY |
| DevOps Safety & Reliability (30%) | HITL gate, P0 escalation, confidence warnings, no dangerous shell hallucinations |
| Code Quality & Architecture (20%) | Modular Python, clean schemas, FastAPI, mock telemetry generator |
| SRE Experience & UI (20%) | Real-time dashboard, AIMS audit log, custom alert injection, post-mortem report |

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **AI:** Groq API (compound-beta-mini) — LLM-powered diagnosis
- **Safety:** HITL gate, AIMS audit logging
- **Frontend:** Vanilla HTML/CSS/JS dashboard
- **Deployment:** Render

## ⚡ Run Locally

```bash
git clone https://github.com/Mahalakshmi2101/sre-agent
cd sre-agent
pip install -r requirements.txt
# Add GROQ_API_KEY to .env file
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/dashboard

## 👩‍💻 Built By

**Mahalakshmi P**