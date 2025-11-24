#!/usr/bin/env python3
"""
Autonomous Brain Coordinator
=============================

Main coordination module that ties everything together.
This is Brain's self-awareness and self-healing core.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional

from .monitor import RailwayLogMonitor
from .classifier import IssueClassifier, ClassifiedIssue, ApprovalLevel
from .logger import ActionLogger, BrainAction


class AutonomousBrain:
    """
    The Autonomous Brain - Self-healing AI coordinator
    
    This is the main class that orchestrates:
    - Self-diagnosis (monitoring)
    - Issue classification
    - Action logging
    - Self-fixing (coming in Phase 2)
    - Self-training (coming in Phase 3)
    - Approval requests (coming in Phase 4)
    """
    
    def __init__(self):
        self.monitor = RailwayLogMonitor()
        self.classifier = IssueClassifier()
        self.logger = ActionLogger()
        
        self.is_running = False
        self.check_interval = 300  # Check every 5 minutes
        
        print("🧠 Autonomous Brain initialized")
        print(f"📊 Check interval: {self.check_interval}s")
    
    async def start(self):
        """Start the autonomous monitoring loop"""
        self.is_running = True
        print("🚀 Autonomous Brain starting...")
        
        while self.is_running:
            try:
                await self.run_diagnostic_cycle()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Error in diagnostic cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop(self):
        """Stop the autonomous monitoring"""
        print("🛑 Stopping Autonomous Brain...")
        self.is_running = False
    
    async def run_diagnostic_cycle(self):
        """
        Run one complete diagnostic cycle
        
        Steps:
        1. Fetch recent logs
        2. Detect issues
        3. Classify issues
        4. Log actions
        5. (Future) Generate fixes
        6. (Future) Apply or request approval
        """
        print(f"\n{'='*60}")
        print(f"🩺 DIAGNOSTIC CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Step 1: Fetch logs
        print("📥 Fetching Railway logs...")
        logs = await self.monitor.get_recent_logs(hours=1)
        print(f"   Found {len(logs)} log lines\n")
        
        # Step 2: Detect issues
        print("🔍 Detecting issues...")
        raw_issues = await self.monitor.detect_errors(logs)
        print(f"   Found {len(raw_issues)} potential issues\n")
        
        if not raw_issues:
            print("✅ No issues detected - System healthy!\n")
            return
        
        # Step 3: Classify issues
        print("🎯 Classifying issues...")
        classified_issues = [self.classifier.classify(issue) for issue in raw_issues]
        
        auto_fixable = self.classifier.get_auto_fixable_issues(classified_issues)
        need_approval = self.classifier.get_approval_required_issues(classified_issues)
        
        print(f"   Auto-fixable: {len(auto_fixable)}")
        print(f"   Need approval: {len(need_approval)}\n")
        
        # Step 4: Log and report
        for issue in classified_issues:
            action = BrainAction(
                timestamp=datetime.now().isoformat(),
                action_type="detected",
                severity=issue.severity.value,
                issue=issue.description,
                proposed_fix=issue.proposed_fix,
                approval_required=issue.approval_required != ApprovalLevel.AUTO_FIX,
                status="pending",
                confidence=issue.confidence
            )
            
            action_id = self.logger.log_action(action)
            
            # Display issue
            severity_emoji = "🔴" if issue.severity.value == "critical" else "🟡" if issue.severity.value == "medium" else "🟢"
            print(f"{severity_emoji} [{issue.severity.value.upper()}] {issue.issue_type}")
            print(f"   Issue: {issue.description}")
            print(f"   Fix: {issue.proposed_fix}")
            print(f"   Confidence: {issue.confidence:.0%}")
            print(f"   Action ID: {action_id}\n")
        
        # Step 5: Summary
        health = await self.monitor.get_health_status()
        print(f"{'='*60}")
        print(f"💚 HEALTH STATUS: {health['health'].upper()}")
        print(f"   Critical: {health['critical_issues']}")
        print(f"   Medium: {health['medium_issues']}")
        print(f"   Minor: {health['minor_issues']}")
        print(f"{'='*60}\n")
    
    async def get_status(self) -> Dict:
        """Get current status of the autonomous brain"""
        stats = self.logger.get_statistics()
        health = await self.monitor.get_health_status()
        pending = self.logger.get_pending_approvals()
        
        return {
            "brain_status": "running" if self.is_running else "stopped",
            "health": health['health'],
            "statistics": stats,
            "pending_approvals": len(pending),
            "last_check": datetime.now().isoformat()
        }
    
    def generate_daily_report(self) -> str:
        """Generate human-readable daily report"""
        return self.logger.generate_daily_report()


async def main():
    """Test the autonomous brain"""
    brain = AutonomousBrain()
    
    # Run one diagnostic cycle
    await brain.run_diagnostic_cycle()
    
    # Get status
    status = await brain.get_status()
    print("\n🧠 BRAIN STATUS:")
    import json
    print(json.dumps(status, indent=2))
    
    # Generate report
    print("\n" + brain.generate_daily_report())


if __name__ == "__main__":
    asyncio.run(main())
