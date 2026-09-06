# diagnostic_agent.py
# Agent 2 — The Diagnostic Agent
# Job: Look at each incident, query mock logs, identify root cause

from triage_agent import triage_agent
from mock_alerts import generate_alerts
import datetime

# ── MOCK LOG DATABASE ──────────────────────────────────────────────────────────
# In real life this would query Datadog, CloudWatch, or Kubernetes logs.
# We simulate it with a dictionary keyed by service name.

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

# ── ROOT CAUSE PATTERNS ────────────────────────────────────────────────────────
# Maps log keywords to root cause diagnoses.
# This is a simple rule-based system — Day 2 we replace this with an LLM call.

ROOT_CAUSE_PATTERNS = {
    "OutOfMemoryError": {
        "cause": "Memory leak after deployment",
        "likely_trigger": "Bad deploy introduced memory leak",
        "safe_fix": "Restart affected pods with memory limits",
        "dangerous_fix": "REBOOT node or DROP connection pool",
    },
    "Max connections reached": {
        "cause": "Database connection pool exhausted",
        "likely_trigger": "Traffic spike or connection leak in application code",
        "safe_fix": "Increase connection pool size, kill idle connections",
        "dangerous_fix": "RESTART database instance",
    },
    "Redis connection timeout": {
        "cause": "Cache layer failure causing auth fallback",
        "likely_trigger": "Redis instance down or network partition",
        "safe_fix": "Flush Redis cache, restart Redis pod",
        "dangerous_fix": "DELETE all session tokens",
    },
    "OOMKilled": {
        "cause": "Container killed by Kubernetes due to memory limit breach",
        "likely_trigger": "Memory limit too low or application memory leak",
        "safe_fix": "Increase pod memory limit, rolling restart",
        "dangerous_fix": "REBOOT entire node",
    },
}


def query_mock_logs(service):
    """Fetch logs for a given service from our mock log database."""
    return MOCK_LOGS.get(service, ["[INFO] No logs found for this service"])


def diagnose_incident(incident):
    """
    Takes one triaged incident, reads its logs, finds root cause.
    Returns a diagnosis dictionary.
    """
    service = incident["service"]
    logs = query_mock_logs(service)

    # Search logs for known patterns
    diagnosis = None
    matched_log = None

    for log_line in logs:
        for pattern, info in ROOT_CAUSE_PATTERNS.items():
            if pattern in log_line:
                diagnosis = info
                matched_log = log_line
                break
        if diagnosis:
            break

    # If no pattern matched, return unknown
    if not diagnosis:
        diagnosis = {
            "cause": "Unknown — requires manual investigation",
            "likely_trigger": "No matching pattern found in logs",
            "safe_fix": "Escalate to senior SRE",
            "dangerous_fix": "None identified",
        }

    return {
        "service": service,
        "severity": incident["severity"],
        "alert_ids": incident["alert_ids"],
        "log_evidence": matched_log,
        "root_cause": diagnosis["cause"],
        "likely_trigger": diagnosis["likely_trigger"],
        "safe_fix": diagnosis["safe_fix"],
        "dangerous_fix": diagnosis["dangerous_fix"],
        "diagnosed_at": datetime.datetime.now().isoformat(),
        "requires_hitl": True if "dangerous_fix" in diagnosis else False,
    }


def diagnostic_agent(triage_results):
    """Runs diagnosis on all triaged incidents."""
    diagnoses = []
    for incident in triage_results:
        diagnosis = diagnose_incident(incident)
        diagnoses.append(diagnosis)
    return diagnoses


# ── PIPELINE: run both agents in sequence ──────────────────────────────────────
if __name__ == "__main__":
    # Step 1: Generate alerts
    alerts = generate_alerts()

    # Step 2: Triage them
    print("=" * 60)
    print("STEP 1: TRIAGE AGENT RUNNING")
    print("=" * 60)
    triaged = triage_agent(alerts)
    print(f"Incidents identified: {len(triaged)}")

    # Step 3: Diagnose each incident
    print("\n" + "=" * 60)
    print("STEP 2: DIAGNOSTIC AGENT RUNNING")
    print("=" * 60)
    diagnoses = diagnostic_agent(triaged)

    for d in diagnoses:
        print(f"\n[{d['severity']}] {d['service']}")
        print(f"  Root Cause   : {d['root_cause']}")
        print(f"  Trigger      : {d['likely_trigger']}")
        print(f"  Safe Fix     : {d['safe_fix']}")
        print(f"  ⚠ Dangerous  : {d['dangerous_fix']}")
        print(f"  Log Evidence : {d['log_evidence']}")
        print(f"  HITL Required: {d['requires_hitl']}")