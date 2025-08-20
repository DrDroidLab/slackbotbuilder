from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import json

from drdroid_debug_toolkit import DroidSDK


CREDENTIALS_FILE_PATH = str(Path(__file__).parent / "credentials.yaml")

# Generic API health check configuration - customize these for your services
API_ENDPOINTS = {
    "Web Application": {
        "url": "https://api.example.com/health",
        "method": "GET",
        "expected_status": 200,
        "timeout": 30,
        "description": "Main web application health endpoint",
        "headers": {
            "User-Agent": "Health-Check-Script/1.0",
            "Accept": "application/json"
        }
    },
    "Database API": {
        "url": "https://db-api.example.com/status",
        "method": "GET", 
        "expected_status": 200,
        "timeout": 15,
        "description": "Database connection status API",
        "headers": {
            "Authorization": "Bearer your-token-here"
        }
    },
    "Authentication Service": {
        "url": "https://auth.example.com/health",
        "method": "GET",
        "expected_status": 200,
        "timeout": 20,
        "description": "Authentication service health check",
        "headers": {}
    },
    "File Storage Service": {
        "url": "https://storage.example.com/health",
        "method": "GET",
        "expected_status": 200,
        "timeout": 25,
        "description": "File storage service status",
        "headers": {}
    },
    "Message Queue": {
        "url": "https://mq.example.com/status",
        "method": "GET",
        "expected_status": 200,
        "timeout": 20,
        "description": "Message queue service health",
        "headers": {}
    }
}

# Health check thresholds
HEALTH_THRESHOLDS = {
    "response_time_critical": 5.0,  # Above 5 seconds is critical
    "response_time_warning": 2.0,   # Above 2 seconds is warning
    "availability_target": 99.9     # Target availability percentage
}


def build_curl_command(endpoint_config: Dict[str, Any]) -> str:
    """Build curl command for the given endpoint configuration."""
    url = endpoint_config["url"]
    method = endpoint_config["method"]
    timeout = endpoint_config["timeout"]
    headers = endpoint_config.get("headers", {})
    
    # Build curl command
    cmd = f"curl -s -w 'HTTPSTATUS:%{{http_code}}|TIME:%{{time_total}}|SIZE:%{{size_download}}'"
    
    # Add method
    if method != "GET":
        cmd += f" -X {method}"
    
    # Add timeout
    cmd += f" --max-time {timeout}"
    
    # Add headers
    for key, value in headers.items():
        if value:  # Only add non-empty headers
            cmd += f" -H '{key}: {value}'"
    
    # Add URL
    cmd += f" '{url}'"
    
    return cmd


def parse_curl_output(output: str) -> Dict[str, Any]:
    """Parse curl output to extract status code, response time, and size."""
    try:
        # Split output by the custom delimiter
        parts = output.split('HTTPSTATUS:')
        if len(parts) != 2:
            return {"status_code": 0, "response_time": 0, "size": 0, "raw_output": output}
        
        # Extract the metrics part
        metrics_part = parts[1]
        metrics_parts = metrics_part.split('|')
        
        result = {}
        for part in metrics_parts:
            if ':' in part:
                key, value = part.split(':', 1)
                if key == 'HTTPSTATUS':
                    result['status_code'] = int(value) if value.isdigit() else 0
                elif key == 'TIME':
                    result['response_time'] = float(value) if value.replace('.', '').isdigit() else 0
                elif key == 'SIZE':
                    result['size'] = int(value) if value.isdigit() else 0
        
        result['raw_output'] = output
        return result
        
    except Exception as e:
        return {"status_code": 0, "response_time": 0, "size": 0, "raw_output": output, "parse_error": str(e)}


def get_health_status(endpoint_config: Dict[str, Any], response_data: Dict[str, Any]) -> str:
    """Determine health status based on response data and thresholds."""
    status_code = response_data.get("status_code", 0)
    response_time = response_data.get("response_time", 0)
    
    # Check status code first
    if status_code != endpoint_config["expected_status"]:
        return "🔴 CRITICAL"
    
    # Check response time
    if response_time > HEALTH_THRESHOLDS["response_time_critical"]:
        return "🔴 CRITICAL"
    elif response_time > HEALTH_THRESHOLDS["response_time_warning"]:
        return "🟡 WARNING"
    else:
        return "🟢 HEALTHY"


def check_api_health(credentials_file_path: str) -> None:
    """Check health of all configured API endpoints using curl commands."""
    sdk = DroidSDK(credentials_file_path)
    
    print(f"🌐 Generic API Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    overall_health = "🟢 HEALTHY"
    endpoint_results = {}
    critical_endpoints = []
    
    for endpoint_name, config in API_ENDPOINTS.items():
        try:
            print(f"\n🔍 Checking {endpoint_name}...")
            print(f"   Description: {config['description']}")
            print(f"   URL: {config['url']}")
            print(f"   Method: {config['method']}")
            print(f"   Expected Status: {config['expected_status']}")
            
            # Build and execute curl command
            curl_cmd = build_curl_command(config)
            print(f"   Executing: {curl_cmd}")
            
            result = sdk.bash.execute_command(command=curl_cmd)
            
            # Parse the result
            response_data = parse_curl_output(result)
            
            # Determine health status
            health_status = get_health_status(config, response_data)
            
            # Display results
            print(f"   Status Code: {response_data.get('status_code', 'N/A')}")
            print(f"   Response Time: {response_data.get('response_time', 0):.3f}s")
            print(f"   Response Size: {response_data.get('size', 0)} bytes")
            print(f"   Health Status: {health_status}")
            
            # Track results
            endpoint_results[endpoint_name] = {
                "health": health_status,
                "response_data": response_data,
                "config": config
            }
            
            # Update overall health
            if "CRITICAL" in health_status:
                critical_endpoints.append(endpoint_name)
                if overall_health == "🟢 HEALTHY":
                    overall_health = "🔴 CRITICAL"
            elif "WARNING" in health_status and overall_health == "🟢 HEALTHY":
                overall_health = "🟡 WARNING"
            
        except Exception as e:
            print(f"   ❌ Error checking {endpoint_name}: {e}")
            endpoint_results[endpoint_name] = {
                "health": "❌ ERROR",
                "response_data": {},
                "config": config,
                "error": str(e)
            }
            if overall_health == "🟢 HEALTHY":
                overall_health = "🟡 WARNING"
    
    # Summary report
    print("\n" + "=" * 80)
    print(f"📊 Overall API Health: {overall_health}")
    print(f"🔍 Endpoints Checked: {len(API_ENDPOINTS)}")
    
    healthy_count = len([r for r in endpoint_results.values() if "HEALTHY" in r["health"]])
    warning_count = len([r for r in endpoint_results.values() if "WARNING" in r["health"]])
    critical_count = len([r for r in endpoint_results.values() if "CRITICAL" in r["health"]])
    error_count = len([r for r in endpoint_results.values() if "ERROR" in r["health"]])
    
    print(f"   🟢 Healthy: {healthy_count}")
    print(f"   🟡 Warning: {warning_count}")
    print(f"   🔴 Critical: {critical_count}")
    print(f"   ❌ Errors: {error_count}")
    
    if critical_endpoints:
        print(f"\n🚨 Critical Endpoints: {', '.join(critical_endpoints)}")
        print("⚠️  Immediate attention required!")
    
    print(f"\n✅ API health check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def export_health_results(credentials_file_path: str, output_file: str) -> None:
    """Export health check results to JSON file."""
    sdk = DroidSDK(credentials_file_path)
    
    try:
        print(f"📤 Exporting health check results...")
        
        results = {}
        for endpoint_name, config in API_ENDPOINTS.items():
            try:
                curl_cmd = build_curl_command(config)
                result = sdk.bash.execute_command(command=curl_cmd)
                response_data = parse_curl_output(result)
                health_status = get_health_status(config, response_data)
                
                results[endpoint_name] = {
                    "health": health_status,
                    "response_data": response_data,
                    "config": config,
                    "checked_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                results[endpoint_name] = {
                    "health": "❌ ERROR",
                    "error": str(e),
                    "config": config,
                    "checked_at": datetime.now().isoformat()
                }
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "endpoints": results
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"   ✅ Results exported to {output_file}")
        
    except Exception as e:
        print(f"   ❌ Error exporting results: {e}")


if __name__ == "__main__":
    check_api_health(CREDENTIALS_FILE_PATH)
    
    # Optionally export results
    # export_health_results(CREDENTIALS_FILE_PATH, "api_health_results.json")
