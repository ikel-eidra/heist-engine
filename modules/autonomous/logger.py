#!/usr/bin/env python3
"""
Action Logger
=============

Logs all Brain actions for transparency and monitoring.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class BrainAction:
    """Represents a single Brain action"""
    timestamp: str
    action_type: str  # "auto_fix", "pending_approval", "approved", "rejected", "training"
    severity: str  # "minor", "medium", "critical"
    issue: str
    proposed_fix: str
    approval_required: bool
    status: str  # "completed", "pending", "failed", "rolled_back"
    result: Optional[str] = None
    error: Optional[str] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class ActionLogger:
    """Logs Brain actions to JSON files for transparency"""
    
    def __init__(self, log_dir: str = "data/brain_actions"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create index file if doesn't exist
        self.index_file = self.log_dir / "index.json"
        if not self.index_file.exists():
            self._create_index()
    
    def _create_index(self):
        """Create index file"""
        index = {
            "created": datetime.now().isoformat(),
            "total_actions": 0,
            "auto_fixes": 0,
            "approvals_requested": 0,
            "approvals_granted": 0,
            "approvals_rejected": 0,
            "failures": 0,
            "rollbacks": 0
        }
        self._save_json(self.index_file, index)
    
    def log_action(self, action: BrainAction) -> str:
        """
        Log a Brain action
        
        Args:
            action: BrainAction to log
            
        Returns:
            Action ID (timestamp-based)
        """
        # Generate action ID
        action_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Save action to daily file
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = self.log_dir / f"{today}.json"
        
        # Load existing actions for today
        if daily_file.exists():
            with open(daily_file, 'r') as f:
                daily_actions = json.load(f)
        else:
            daily_actions = []
        
        # Add new action
        action_dict = action.to_dict()
        action_dict['action_id'] = action_id
        daily_actions.append(action_dict)
        
        # Save updated daily file
        self._save_json(daily_file, daily_actions)
        
        # Update index
        self._update_index(action)
        
        return action_id
    
    def _update_index(self, action: BrainAction):
        """Update the index with action statistics"""
        with open(self.index_file, 'r') as f:
            index = json.load(f)
        
        index['total_actions'] += 1
        
        if action.action_type == "auto_fix":
            index['auto_fixes'] += 1
        elif action.action_type == "pending_approval":
            index['approvals_requested'] += 1
        elif action.action_type == "approved":
            index['approvals_granted'] += 1
        elif action.action_type == "rejected":
            index['approvals_rejected'] += 1
        
        if action.status == "failed":
            index['failures'] += 1
        elif action.status == "rolled_back":
            index['rollbacks'] += 1
        
        self._save_json(self.index_file, index)
    
    def get_recent_actions(self, days: int = 7) -> List[Dict]:
        """Get actions from the last N days"""
        actions = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            daily_file = self.log_dir / f"{date_str}.json"
            
            if daily_file.exists():
                with open(daily_file, 'r') as f:
                    daily_actions = json.load(f)
                    actions.extend(daily_actions)
        
        # Sort by timestamp (newest first)
        actions.sort(key=lambda x: x['timestamp'], reverse=True)
        return actions
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        with open(self.index_file, 'r') as f:
            return json.load(f)
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all pending approval requests"""
        recent = self.get_recent_actions(days=30)
        return [
            action for action in recent 
            if action['action_type'] == 'pending_approval' 
            and action['status'] == 'pending'
        ]
    
    def _save_json(self, filepath: Path, data):
        """Save data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_daily_report(self, date: Optional[str] = None) -> str:
        """
        Generate human-readable report for a specific day
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Formatted report string
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        daily_file = self.log_dir / f"{date}.json"
        
        if not daily_file.exists():
            return f"No actions logged for {date}"
        
        with open(daily_file, 'r') as f:
            actions = json.load(f)
        
        report = f"""
╔══════════════════════════════════════════════════════════
║ 🧠 BRAIN ACTIVITY REPORT - {date}
╚══════════════════════════════════════════════════════════

📊 SUMMARY:
   Total Actions: {len(actions)}
   Auto-Fixes: {sum(1 for a in actions if a['action_type'] == 'auto_fix')}
   Approval Requests: {sum(1 for a in actions if a['action_type'] == 'pending_approval')}
   Completed: {sum(1 for a in actions if a['status'] == 'completed')}
   Failed: {sum(1 for a in actions if a['status'] == 'failed')}

📝 ACTIONS:
"""
        
        for action in actions:
            status_emoji = "✅" if action['status'] == 'completed' else "⏳" if action['status'] == 'pending' else "❌"
            report += f"\n   {status_emoji} [{action['timestamp']}] {action['action_type'].upper()}\n"
            report += f"      Issue: {action['issue']}\n"
            report += f"      Fix: {action['proposed_fix'][:80]}...\n"
        
        return report


if __name__ == "__main__":
    from datetime import timedelta
    
    # Test the logger
    logger = ActionLogger()
    
    # Create test actions
    test_action = BrainAction(
        timestamp=datetime.now().isoformat(),
        action_type="auto_fix",
        severity="minor",
        issue="Invalid Telegram channel username",
        proposed_fix="Remove invalid channel from config",
        approval_required=False,
        status="completed",
        result="Successfully removed invalid channel",
        confidence=0.95
    )
    
    action_id = logger.log_action(test_action)
    print(f"✅ Logged action: {action_id}\n")
    
    # Get statistics
    stats = logger.get_statistics()
    print("📊 Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Generate daily report
    print("\n" + logger.generate_daily_report())
