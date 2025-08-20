from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta

from drdroid_debug_toolkit import DroidSDK


CREDENTIALS_FILE_PATH = str(Path(__file__).parent / "credentials.yaml")

# Generic SLO monitoring configuration - customize these values for your environment
SLO_SERVICES = {
    "Web Service A": {
        "dashboard_id": "101",
        "panel_id": "1",
        "description": "Main web application availability",
        "datasource_uid": "prometheus",
        "query": "sum(rate(http_requests_total{status=~\"(2|3)[0-9]+\", service=\"web-service-a\"}[5m])) / sum(rate(http_requests_total{status=~\"(2|3|5)[0-9]+\", service=\"web-service-a\"}[5m])) * 100"
    },
    "API Gateway": {
        "dashboard_id": "102",
        "panel_id": "2",
        "description": "API gateway success rate",
        "datasource_uid": "prometheus",
        "query": "sum(rate(api_requests_total{status=~\"(2|3)[0-9]+\", gateway=\"main\"}[5m])) / sum(rate(api_requests_total{status=~\"(2|3|5)[0-9]+\", gateway=\"main\"}[5m])) * 100"
    },
    "Database Service": {
        "dashboard_id": "103",
        "panel_id": "3",
        "description": "Database connection success rate",
        "datasource_uid": "prometheus",
        "query": "sum(rate(db_connections_total{status=\"success\"}[5m])) / sum(rate(db_connections_total[5m])) * 100"
    },
    "Cache Service": {
        "dashboard_id": "104",
        "panel_id": "4",
        "description": "Cache hit ratio",
        "datasource_uid": "prometheus",
        "query": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100"
    },
    "Load Balancer": {
        "dashboard_id": "105",
        "panel_id": "5",
        "description": "Load balancer health check",
        "datasource_uid": "prometheus",
        "query": "up{job=\"load-balancer-health\"}"
    },
    "Message Queue": {
        "dashboard_id": "106",
        "panel_id": "6",
        "description": "Message processing success rate",
        "datasource_uid": "prometheus",
        "query": "sum(rate(message_processed_total{status=\"success\"}[5m])) / sum(rate(message_received_total[5m])) * 100"
    }
}

# SLO thresholds - customize these based on your requirements
SLO_THRESHOLDS = {
    "critical": 95.0,  # Below 95% is critical
    "warning": 99.0,   # Below 99% is warning
    "target": 99.9     # Target SLO
}


def get_slo_status(slo_value: float) -> str:
    """Determine SLO status based on thresholds."""
    if slo_value < SLO_THRESHOLDS["critical"]:
        return "🔴 CRITICAL"
    elif slo_value < SLO_THRESHOLDS["warning"]:
        return "🟡 WARNING"
    elif slo_value < SLO_THRESHOLDS["target"]:
        return "🟠 DEGRADED"
    else:
        return "🟢 HEALTHY"


def monitor_global_slos(credentials_file_path: str, duration_minutes: int = 60) -> None:
    """Monitor all configured SLOs using Grafana queries."""
    sdk = DroidSDK(credentials_file_path)
    
    print(f"🔍 Generic SLO Monitoring - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Monitoring period: {duration_minutes} minutes")
    print("=" * 80)
    
    overall_status = "🟢 HEALTHY"
    critical_services = []
    
    for service_name, config in SLO_SERVICES.items():
        try:
            print(f"\n📊 Checking {service_name} SLO...")
            print(f"   Description: {config['description']}")
            
            # Query Grafana panel metric
            result = sdk.grafana.query_dashboard_panel(
                dashboard_id=config["dashboard_id"],
                panel_id=config["panel_id"],
                datasource_uid=config["datasource_uid"],
                queries=config["query"]
            )
            
            # Extract SLO value from result
            # Note: Actual result structure may vary - adjust parsing as needed
            slo_value = 99.5  # Placeholder - extract from actual result
            
            status = get_slo_status(slo_value)
            print(f"   {service_name}: {slo_value:.2f}% - {status}")
            
            # Track critical services
            if slo_value < SLO_THRESHOLDS["critical"]:
                critical_services.append(service_name)
                if overall_status == "🟢 HEALTHY":
                    overall_status = "🔴 CRITICAL"
            
        except Exception as e:
            print(f"   ❌ Error monitoring {service_name}: {e}")
            if overall_status == "🟢 HEALTHY":
                overall_status = "🟡 WARNING"
    
    print("\n" + "=" * 80)
    print(f"📈 Overall SLO Status: {overall_status}")
    
    if critical_services:
        print(f"🚨 Critical Services: {', '.join(critical_services)}")
        print("⚠️  Immediate attention required!")
    
    print(f"\n✅ SLO monitoring completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    monitor_global_slos(
        credentials_file_path=CREDENTIALS_FILE_PATH,
        duration_minutes=60
    )
