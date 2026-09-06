# ai_diagnostic_agent.py
from groq import Groq
from dotenv import load_dotenv
import os
import datetime

from triage_agent import triage_agent
from mock_alerts import generate_alerts

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MOCK_LOGS = {
    "payment-api": [
        "[ERROR] 2026-09-04T10:45:00 OutOfMemoryError: heap space exceeded after deploy v2.3.1",
        "[WARN]  2026-09-04T10:46:00 GC overhead limit exceeded, response times degrading",
        "[ERROR] 2026-09-04T10:47:00 Thread pool exhausted, dropping requests",
    ],
    "user-db": [
        "[ERROR] 2026-09-04T10:44:00 Max connections reached: 500/500",
        "[WARN]  2026-09-04T10:44:30 Replication slave lagging by 35 seconds",
        "[ERROR] 2026-09-04T10:45:00 Deadlock detected on table: user_sessions",
    ],
    "auth-service": [
        "[ERROR] 2026-09-04T10:43:00 Redis connection timeout after 5000ms",
        "[ERROR] 2026-09-04T10:43:30 Token validation failing: cache miss rate 98%",
        "[WARN]  2026-09-04T10:44:00 Fallback to DB auth, latency spike expected",
    ],
    "k8s-node-01": [
        "[ERROR] 2026-09-04T10:42:00 OOMKilled: container payment-worker exceeded 2Gi limit",
        "[WARN]  2026-09-04T10:42:30 Node memory pressure: 95% utilized",
        "[ERROR] 2026-09-04T10:43:00 Pod evicted: insufficient memory on node",
    ],
}

DANGEROUS_COMMANDS = ["DELETE", "DROP", "REBOOT", "RESTART", "KILL", "TRUNCATE", "FORMAT"]

def is_dangerous(action):
    return any(cmd in action.upper() for cmd in DANGEROUS_COMMANDS)

def query_logs(service):
    logs = MOCK_LOGS.get(service, ["No logs found"])
    return "\n".join(logs)

def ai_diagnose(incident):
    service = incident["service"]
    severity = incident["severity"]
    messages = incident["messages"]
    logs = query_logs(service)

    prompt = f"""You are a senior SRE engineer. Analyze this incident and reply with exactly 5 lines, no extra text.

Service: {service}
Severity: {severity}
Alerts: {messages}
Logs:
{logs}

Reply in exactly this format (fill in real values, no brackets):
ROOT_CAUSE: <what is actually wrong based on the logs>
TRIGGER: <what caused this based on the logs>
SAFE_FIX: <one safe remediation step>
DANGEROUS_FIX: RESTART the {service} service instances to clear corrupted state
CONFIDENCE: HIGH"""

    response = client.chat.completions.create(
       model="compound-beta-mini",
        messages=[
            {"role": "system", "content": "You are a senior SRE engineer. You must replace ALL placeholder text in angle brackets with real technical values based on the logs provided. Never output angle brackets in your response."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=300
    )
    return response.choices[0].message.content

def parse_ai_response(ai_text):
    result = {}
    # Clean any thinking tags the model might add
    clean = ai_text
    if "</think>" in clean:
        clean = clean.split("</think>")[-1]
    for line in clean.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result

def ai_diagnostic_agent(triage_results):
    diagnoses = []
    for incident in triage_results:
        print(f"  Diagnosing {incident['service']}...")
        ai_response = ai_diagnose(incident)
        parsed = parse_ai_response(ai_response)
        dangerous_fix = parsed.get("DANGEROUS_FIX", f"RESTART {incident['service']} service")
        diagnosis = {
            "service": incident["service"],
            "severity": incident["severity"],
            "alert_ids": incident["alert_ids"],
            "messages": incident["messages"],
            "root_cause": parsed.get("ROOT_CAUSE", "Unknown — check logs manually"),
            "trigger": parsed.get("TRIGGER", "Unknown"),
            "safe_fix": parsed.get("SAFE_FIX", "Escalate to senior SRE"),
            "dangerous_fix": dangerous_fix,
            "confidence": parsed.get("CONFIDENCE", "MEDIUM"),
            "requires_hitl": is_dangerous(dangerous_fix),
            "diagnosed_at": datetime.datetime.now().isoformat(),
        }
        diagnoses.append(diagnosis)
    return diagnoses


if __name__ == "__main__":
    print("=" * 60)
    print("STEP 1: GENERATING + TRIAGING ALERTS")
    print("=" * 60)
    alerts = generate_alerts()
    triaged = triage_agent(alerts)
    print(f"Incidents to diagnose: {len(triaged)}")

    print("\n" + "=" * 60)
    print("STEP 2: AI DIAGNOSTIC AGENT RUNNING")
    print("=" * 60)
    diagnoses = ai_diagnostic_agent(triaged)

    print("\n" + "=" * 60)
    print("AI DIAGNOSIS RESULTS")
    print("=" * 60)

    for d in diagnoses:
        print(f"\n[{d['severity']}] {d['service']} (Confidence: {d['confidence']})")
        print(f"  Root Cause  : {d['root_cause']}")
        print(f"  Trigger     : {d['trigger']}")
        print(f"  Safe Fix    : {d['safe_fix']}")
        print(f"  ⚠ Dangerous : {d['dangerous_fix']}")
        print(f"  HITL Gate   : {'🔴 BLOCKED — needs human approval' if d['requires_hitl'] else '🟢 Safe to auto-execute'}")