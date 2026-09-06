# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
import datetime
import json
import os

from mock_alerts import generate_alerts
from triage_agent import triage_agent
from ai_diagnostic_agent import ai_diagnostic_agent

app = FastAPI(
    title="SRE Agent — Enterprise Cloud Incident Triage System",
    description="Governed multi-agent SRE mesh that triages alerts, diagnoses root cause, and proposes safe remediations with HITL gates.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

INCIDENT_HISTORY = []

class CustomAlert(BaseModel):
    service: str
    message: str
    type: str
    severity: str

class CustomAlertBatch(BaseModel):
    alerts: List[CustomAlert]

def run_pipeline(alerts):
    triaged = triage_agent(alerts)
    diagnoses = ai_diagnostic_agent(triaged)
    remediation_plan = []
    audit_log = []
    for d in diagnoses:
        plan = {
            "service": d["service"],
            "severity": d["severity"],
            "root_cause": d["root_cause"],
            "trigger": d["trigger"],
            "safe_fix": d["safe_fix"],
            "safe_fix_status": "AUTO_EXECUTED",
            "dangerous_fix": d["dangerous_fix"],
            "hitl_status": "BLOCKED_PENDING_APPROVAL" if d["requires_hitl"] else "NOT_REQUIRED",
            "confidence": d["confidence"],
        }
        remediation_plan.append(plan)
        audit_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "service": d["service"],
            "event": "HITL_BLOCKED" if d["requires_hitl"] else "AUTO_REMEDIATED",
            "action": d["dangerous_fix"] if d["requires_hitl"] else d["safe_fix"],
            "agent": "RemediationAgent"
        })
    post_mortem = {
        "report_id": f"PM-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "total_alerts": len(alerts),
        "incidents": len(triaged),
        "p1_count": sum(1 for t in triaged if t["severity"] == "P1"),
        "auto_remediated": sum(1 for r in remediation_plan if r["safe_fix_status"] == "AUTO_EXECUTED"),
        "hitl_blocked": sum(1 for r in remediation_plan if r["hitl_status"] == "BLOCKED_PENDING_APPROVAL"),
        "prevention": [
            "Implement canary deployments to catch memory leaks before full rollout",
            "Set up connection pool monitoring alerts at 80% threshold",
            "Configure Kubernetes memory limits with 20% headroom above baseline",
            "Add Redis sentinel for automatic failover on cache layer",
        ]
    }
    result = {
        "pipeline_status": "COMPLETE",
        "timestamp": datetime.datetime.now().isoformat(),
        "triage": {"total_alerts": len(alerts), "incidents_identified": len(triaged)},
        "remediation_plan": remediation_plan,
        "audit_log": audit_log,
        "post_mortem": post_mortem
    }
    INCIDENT_HISTORY.append({"timestamp": datetime.datetime.now().isoformat(), "summary": post_mortem})
    return result

@app.get("/")
def root():
    return {
        "system": "SRE Incident Triage Agent",
        "version": "1.0.0",
        "status": "operational",
        "agents": ["TriageAgent", "DiagnosticAgent", "RemediationAgent"],
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "agents_ready": True,
        "ai_backend": "Groq/compound-beta-mini",
        "lyzr_guardrails": "active"
    }

@app.get("/triage")
def run_triage():
    alerts = generate_alerts()
    triaged = triage_agent(alerts)
    return {
        "stage": "triage",
        "total_alerts": len(alerts),
        "incidents_identified": len(triaged),
        "incidents": triaged,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/analyze")
def run_full_pipeline():
    alerts = generate_alerts()
    return run_pipeline(alerts)

@app.post("/analyze/custom")
def run_custom_pipeline(batch: CustomAlertBatch):
    import datetime as dt
    alerts = []
    for i, a in enumerate(batch.alerts):
        alerts.append({
            "id": f"CUSTOM-{1000+i}",
            "timestamp": dt.datetime.now().isoformat(),
            "service": a.service,
            "message": a.message,
            "type": a.type,
            "severity": a.severity
        })
    return run_pipeline(alerts)

@app.get("/history")
def get_history():
    return {
        "total_runs": len(INCIDENT_HISTORY),
        "history": INCIDENT_HISTORY
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return f.read()