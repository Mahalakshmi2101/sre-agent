# triage_agent.py
import random
import datetime
from mock_alerts import generate_alerts

# Tracks how many times each service has been flagged across all runs
SERVICE_HISTORY = {}

def triage_agent(alerts):
    severity_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
    
    grouped = {}
    for alert in alerts:
        service = alert["service"]
        if service not in grouped:
            grouped[service] = []
        grouped[service].append(alert)

    # Update service history
    for service in grouped:
        SERVICE_HISTORY[service] = SERVICE_HISTORY.get(service, 0) + len(grouped[service])

    triage_results = []
    for service, service_alerts in grouped.items():
        worst_severity = min(
            service_alerts,
            key=lambda a: severity_rank.get(a["severity"], 4)
        )["severity"]

        # SEVERITY ESCALATION: if service has 3+ total alerts historically, upgrade to P0
        total_hits = SERVICE_HISTORY.get(service, 0)
        escalated = False
        if total_hits >= 3 and worst_severity != "P0":
            worst_severity = "P0"
            escalated = True

        result = {
            "service": service,
            "alert_count": len(service_alerts),
            "severity": worst_severity,
            "alert_ids": [a["id"] for a in service_alerts],
            "messages": [a["message"] for a in service_alerts],
            "status": "INCIDENT_OPEN",
            "escalated": escalated,
            "total_historical_alerts": total_hits
        }
        triage_results.append(result)

    triage_results.sort(key=lambda x: severity_rank.get(x["severity"], 4))
    return triage_results


if __name__ == "__main__":
    alerts = generate_alerts()
    results = triage_agent(alerts)
    for r in results:
        flag = "⚠️ ESCALATED TO P0" if r["escalated"] else ""
        print(f"[{r['severity']}] {r['service']} — {r['alert_count']} alerts — history: {r['total_historical_alerts']} {flag}")