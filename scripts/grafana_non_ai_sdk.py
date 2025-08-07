#!/usr/bin/env python3
"""
Simple Grafana SDK Usage Examples
DroidSpace SDK v2 Integration for Slack Bot Builder
"""

import os
import sys
from datetime import datetime, timedelta
# Add the current directory to Python path
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Simple Grafana SDK usage examples"""
    print("🔍 Grafana SDK Examples")
    
    try:
        from drdroid_debug_toolkit.sdk_v2 import DroidSDK
        
        # Initialize SDK with credentials
        credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.yaml")
        sdk = DroidSDK(credentials_path)
        
        # Get Grafana SDK instance
        grafana = sdk.grafana
        
        # Example 1: Query Prometheus metrics
        print("\n📊 Example 1: Query Prometheus metrics")
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=10)
        
        result = grafana.query_prometheus(
            datasource_uid="prometheus",
            query="up",
            start_time=start_time,
            end_time=end_time,
            duration_minutes=10,
            interval=30
        )
        print(f"✅ Prometheus query result: {len(str(result))} characters")
        
        # Example 2: Get dashboard variables
        print("\n📋 Example 2: Fetch dashboard variables")
        try:
            variables = grafana.fetch_dashboard_variables(
                dashboard_uid="d8bcc485-3616-4ded-a33b-553da1e95510"
            )
            print(f"✅ Dashboard variables: {len(str(variables))} characters")
        except Exception as e:
            print(f"⚠️  Dashboard variables failed: {e}")
        
        # Example 3: Execute all panels from a dashboard
        print("\n📈 Example 3: Execute all dashboard panels")
        try:
            panels_result = grafana.execute_all_dashboard_panels(
                dashboard_uid="d8bcc485-3616-4ded-a33b-553da1e95510",
                start_time=start_time,
                end_time=end_time,
                duration_minutes=10,
                interval=30,
                template_variables={
                    "service_name": "productcatalogservice"
                }
            )
            print(f"✅ Dashboard panels: {len(panels_result)} results")
        except Exception as e:
            print(f"⚠️  Dashboard panels failed: {e}")
        
        # Example 4: Query specific dashboard panel
        print("\n🎯 Example 4: Query specific dashboard panel")
        try:
            panel_result = grafana.query_dashboard_panel(
                dashboard_id="1",
                panel_id="1",
                datasource_uid="prometheus",
                queries=["go_memstats_heap_sys_bytes{service=\"productcatalogservice\"}"],
                start_time=start_time,
                end_time=end_time,
                duration_minutes=10
            )
            print(f"✅ Panel query: {len(str(panel_result))} characters")
        except Exception as e:
            print(f"⚠️  Panel query failed: {e}")

        print("\n✅ All Grafana SDK examples completed!")
        
    except ImportError as e:
        print(f"❌ Failed to import DroidSDK: {e}")
        print("💡 Make sure to install the SDK: pip install git+https://github.com/DrDroidLab/drdroid-debug-toolkit.git")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 