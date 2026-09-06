import random
import datetime

def generate_alerts():
    alert_templates = [
        {"service": "payment-api", "message": "CPU usage > 95%", "type": "cpu_spike"},
        {"service": "payment-api", "message": "Response latency > 5000ms", "type": "latency"},
        {"service": "user-db", "message": "Connection pool exhausted", "type": "db_connection"},
        {"service": "user-db", "message": "Replication lag > 30s", "type": "db_lag"},
        {"service": "auth-service", "message": "Error rate > 50%", "type": "error_rate"},
        {"service": "k8s-node-01", "message": "OOMKilled: memory limit exceeded", "type": "memory"},
    ]
    
    alerts = []
    for i, template in enumerate(alert_templates):
        alert = {
            "id": f"ALT-{1000 + i}",
            "timestamp": datetime.datetime.now().isoformat(),
            "service": template["service"],
            "message": template["message"],
            "type": template["type"],
            "severity": random.choice(["P1", "P1", "P2", "P3"])
        }
        alerts.append(alert)
    
    return alerts

if __name__ == "__main__":
    alerts = generate_alerts()
    for alert in alerts:
        print(alert)