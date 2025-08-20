from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json

from drdroid_debug_toolkit import DroidSDK


CREDENTIALS_FILE_PATH = str(Path(__file__).parent / "credentials.yaml")

# Generic dashboard monitoring configuration - customize these for your environment
DASHBOARDS_TO_MONITOR = {
    "Infrastructure Overview": {
        "dashboard_id": "1001",
        "description": "System health and resource utilization",
        "panels_to_check": [1, 2, 3, 4, 5],
        "datasource_uid": "prometheus",
        "default_query": "up"
    },
    "Application Metrics": {
        "dashboard_id": "1002", 
        "description": "Application performance and error rates",
        "panels_to_check": [1, 2, 3],
        "datasource_uid": "prometheus",
        "default_query": "up"
    },
    "Database Performance": {
        "dashboard_id": "1003",
        "description": "Database connection pools and query performance",
        "panels_to_check": [1, 2, 3, 4],
        "datasource_uid": "prometheus",
        "default_query": "up"
    },
    "Network Monitoring": {
        "dashboard_id": "1004",
        "description": "Network latency and packet loss",
        "panels_to_check": [1, 2],
        "datasource_uid": "prometheus",
        "default_query": "up"
    }
}

# Monitoring thresholds - customize based on your requirements
THRESHOLDS = {
    "critical": 80.0,    # Below 80% is critical
    "warning": 90.0,     # Below 90% is warning
    "target": 95.0       # Target performance
}


def get_performance_status(value: float) -> str:
    """Determine performance status based on thresholds."""
    if value < THRESHOLDS["critical"]:
        return "🔴 CRITICAL"
    elif value < THRESHOLDS["warning"]:
        return "🟡 WARNING"
    elif value < THRESHOLDS["target"]:
        return "🟠 DEGRADED"
    else:
        return "🟢 HEALTHY"


def monitor_dashboards(credentials_file_path: str) -> None:
    """Monitor multiple Grafana dashboards for overall health."""
    sdk = DroidSDK(credentials_file_path)
    
    print(f"📊 Generic Dashboard Monitoring - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    overall_health = "🟢 HEALTHY"
    dashboard_results = {}
    
    # First, get all available dashboards
    try:
        print("🔍 Fetching available dashboards...")
        all_dashboards = sdk.grafana.fetch_all_dashboards()
        print(f"   Found {len(all_dashboards)} dashboards")
    except Exception as e:
        print(f"   ❌ Error fetching dashboards: {e}")
        all_dashboards = []
    
    # Monitor specific dashboards
    for dashboard_name, config in DASHBOARDS_TO_MONITOR.items():
        try:
            print(f"\n📈 Monitoring {dashboard_name}...")
            print(f"   Description: {config['description']}")
            print(f"   Dashboard ID: {config['dashboard_id']}")
            
            # Get dashboard configuration
            dashboard_config = sdk.grafana.get_dashboard_config(config["dashboard_id"])
            print(f"   ✅ Dashboard config retrieved")
            
            # Check specific panels
            panel_results = []
            for panel_id in config["panels_to_check"]:
                try:
                    # Try using query_prometheus with minimal parameters
                    panel_data = sdk.grafana.query_prometheus(
                        query=config["default_query"],
                        datasource_uid=config["datasource_uid"]
                    )
                    
                    # Extract metric value (placeholder - adjust based on actual response)
                    metric_value = 92.5  # This would come from panel_data
                    status = get_performance_status(metric_value)
                    
                    panel_results.append({
                        "panel_id": panel_id,
                        "value": metric_value,
                        "status": status
                    })
                    
                    print(f"      Panel {panel_id}: {metric_value:.1f}% - {status}")
                    
                except Exception as e:
                    print(f"      ❌ Error querying panel {panel_id}: {e}")
                    panel_results.append({
                        "panel_id": panel_id,
                        "value": 0,
                        "status": "❌ ERROR"
                    })
            
            # Determine dashboard health
            healthy_panels = [p for p in panel_results if "HEALTHY" in p["status"]]
            critical_panels = [p for p in panel_results if "CRITICAL" in p["status"]]
            
            if critical_panels:
                dashboard_health = "🔴 CRITICAL"
                if overall_health == "🟢 HEALTHY":
                    overall_health = "🔴 CRITICAL"
            elif len(healthy_panels) < len(panel_results):
                dashboard_health = "🟡 WARNING"
                if overall_health == "🟢 HEALTHY":
                    overall_health = "🟡 WARNING"
            else:
                dashboard_health = "🟢 HEALTHY"
            
            dashboard_results[dashboard_name] = {
                "health": dashboard_health,
                "panels": panel_results,
                "overall_score": len(healthy_panels) / len(panel_results) * 100
            }
            
            print(f"   📊 Dashboard Health: {dashboard_health}")
            
        except Exception as e:
            print(f"   ❌ Error monitoring {dashboard_name}: {e}")
            dashboard_results[dashboard_name] = {
                "health": "❌ ERROR",
                "panels": [],
                "overall_score": 0
            }
    
    # Summary report
    print("\n" + "=" * 80)
    print(f"📈 Overall Monitoring Status: {overall_health}")
    print("\n📋 Dashboard Summary:")
    
    for dashboard_name, result in dashboard_results.items():
        print(f"   {dashboard_name}: {result['health']} (Score: {result['overall_score']:.1f}%)")
    
    print(f"\n✅ Dashboard monitoring completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    monitor_dashboards(CREDENTIALS_FILE_PATH)
