#!/usr/bin/env python3
"""
Railway Log Monitor
===================

Reads and analyzes Railway deployment logs to detect issues.
This is the foundation of Brain's self-diagnosis capability.
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json


class RailwayLogMonitor:
    """Monitors Railway deployment logs for errors and issues"""
    
    def __init__(self):
        self.railway_token = os.getenv('RAILWAY_TOKEN')
        self.project_id = os.getenv('RAILWAY_PROJECT_ID')
        self.service_id = os.getenv('RAILWAY_SERVICE_ID')
        
        if not self.railway_token:
            raise ValueError("RAILWAY_TOKEN not found in environment")
            
        self.base_url = "https://backboard.railway.app/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.railway_token}",
            "Content-Type": "application/json"
        }
    
    async def get_recent_logs(self, hours: int = 1) -> List[str]:
        """
        Fetch recent deployment logs from Railway
        
        Args:
            hours: Number of hours of logs to fetch
            
        Returns:
            List of log lines
        """
        query = """
        query GetDeploymentLogs($deploymentId: String!) {
            deployment(id: $deploymentId) {
                logs {
                    timestamp
                    message
                }
            }
        }
        """
        
        # Get latest deployment ID first
        deployment_id = await self._get_latest_deployment_id()
        
        if not deployment_id:
            return []
        
        variables = {"deploymentId": deployment_id}
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get('data', {}).get('deployment', {}).get('logs', [])
                
                # Filter by time
                cutoff = datetime.now() - timedelta(hours=hours)
                filtered_logs = [
                    log['message'] 
                    for log in logs 
                    if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > cutoff
                ]
                
                return filtered_logs
            else:
                print(f"❌ Railway API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching logs: {e}")
            return []
    
    async def _get_latest_deployment_id(self) -> Optional[str]:
        """Get the ID of the latest deployment"""
        query = """
        query GetLatestDeployment($serviceId: String!) {
            service(id: $serviceId) {
                deployments(first: 1) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
        """
        
        variables = {"serviceId": self.service_id}
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                edges = data.get('data', {}).get('service', {}).get('deployments', {}).get('edges', [])
                if edges:
                    return edges[0]['node']['id']
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting deployment ID: {e}")
            return None
    
    async def detect_errors(self, logs: List[str]) -> List[Dict]:
        """
        Analyze logs to detect errors and issues
        
        Args:
            logs: List of log lines
            
        Returns:
            List of detected issues with details
        """
        issues = []
        
        error_patterns = {
            "python_exception": r"(Traceback|Exception|Error):",
            "telegram_error": r"(telethon|telegram).*error",
            "api_error": r"(API|HTTP).*([4-5]\d{2})",
            "connection_error": r"(connection|timeout|refused)",
            "import_error": r"ModuleNotFoundError|ImportError",
            "syntax_error": r"SyntaxError",
            "runtime_error": r"RuntimeError|ValueError|KeyError",
        }
        
        for log_line in logs:
            log_lower = log_line.lower()
            
            # Check each pattern
            for error_type, pattern in error_patterns.items():
                if any(keyword in log_lower for keyword in pattern.lower().split('|')):
                    issues.append({
                        "type": error_type,
                        "timestamp": datetime.now().isoformat(),
                        "log_line": log_line,
                        "severity": self._assess_severity(error_type, log_line)
                    })
        
        return issues
    
    def _assess_severity(self, error_type: str, log_line: str) -> str:
        """
        Assess the severity of an error
        
        Returns:
            "critical", "medium", or "minor"
        """
        critical_keywords = ["crash", "fatal", "critical", "failed to start"]
        medium_keywords = ["error", "exception", "failed", "timeout"]
        
        log_lower = log_line.lower()
        
        if any(kw in log_lower for kw in critical_keywords):
            return "critical"
        elif any(kw in log_lower for kw in medium_keywords):
            return "medium"
        else:
            return "minor"
    
    async def get_health_status(self) -> Dict:
        """
        Get overall health status of the deployment
        
        Returns:
            Health status dict with metrics
        """
        logs = await self.get_recent_logs(hours=1)
        issues = await self.detect_errors(logs)
        
        critical_issues = [i for i in issues if i['severity'] == 'critical']
        medium_issues = [i for i in issues if i['severity'] == 'medium']
        minor_issues = [i for i in issues if i['severity'] == 'minor']
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_logs": len(logs),
            "total_issues": len(issues),
            "critical_issues": len(critical_issues),
            "medium_issues": len(medium_issues),
            "minor_issues": len(minor_issues),
            "health": "critical" if critical_issues else "degraded" if medium_issues else "healthy",
            "issues": issues[:10]  # Return top 10 issues
        }


if __name__ == "__main__":
    import asyncio
    
    async def test_monitor():
        monitor = RailwayLogMonitor()
        
        print("🔍 Fetching Railway logs...")
        logs = await monitor.get_recent_logs(hours=1)
        print(f"📊 Found {len(logs)} log lines\n")
        
        print("🩺 Detecting issues...")
        issues = await monitor.detect_errors(logs)
        print(f"⚠️  Found {len(issues)} issues\n")
        
        print("💚 Health Status:")
        health = await monitor.get_health_status()
        print(json.dumps(health, indent=2))
    
    asyncio.run(test_monitor())
