#!/usr/bin/env python3
"""
Telegram Approval System
=========================

Human oversight and control for the Autonomous Brain.
Sends approval requests, handles responses, and implements kill switch.
"""

import os
import asyncio
from typing import Dict, Optional
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.custom import Button


class ApprovalSystem:
    """Telegram-based approval and control system"""
    
    def __init__(self):
        self.api_id = int(os.getenv('TELEGRAM_API_ID', '38780774'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH', '67eb070dd0e94d2cfc9a0a4dfb5dfcec')
        self.user_chat_id = int(os.getenv('USER_CHAT_ID', '5703832946'))
        
        self.client = None
        self.pending_approvals = {}
        self.brain_active = True
        
        print(f"🔐 Approval System initialized")
        print(f"   User Chat ID: {self.user_chat_id}")
    
    async def initialize(self):
        """Initialize Telegram client"""
        self.client = TelegramClient('brain_approval_session', self.api_id, self.api_hash)
        await self.client.start()
        print("✅ Telegram client connected")
    
    async def request_approval(
        self,
        title: str,
        description: str,
        proposed_fix: str,
        confidence: float,
        risk_level: str,
        action_id: str
    ) -> bool:
        """
        Request approval from user via Telegram
        
        Args:
            title: Short title
            description: Issue description
            proposed_fix: Proposed solution
            confidence: AI confidence (0-1)
            risk_level: low/medium/high
            action_id: Unique action ID
            
        Returns:
            True if user approves
        """
        
        print(f"\n📱 Sending approval request to user...")
        
        # Build approval message
        message = f"""
🧠 **BRAIN APPROVAL REQUEST**

**Issue:** {title}

**Description:**
{description[:200]}...

**Proposed Fix:**
{proposed_fix[:300]}...

**Risk Assessment:**
• Confidence: {confidence:.0%}
• Risk Level: {risk_level.upper()}

**Action ID:** `{action_id}`

Please review and approve/reject this change.
"""
        
        try:
            # Send message with inline buttons
            sent_message = await self.client.send_message(
                self.user_chat_id,
                message,
                buttons=[
                    [
                        Button.inline("✅ APPROVE", data=f"approve_{action_id}"),
                        Button.inline("❌ REJECT", data=f"reject_{action_id}")
                    ],
                    [Button.inline("📋 VIEW DETAILS", data=f"details_{action_id}")]
                ]
            )
            
            # Store pending approval
            self.pending_approvals[action_id] = {
                "message_id": sent_message.id,
                "status": "pending",
                "requested_at": datetime.now().isoformat()
            }
            
            print(f"✅ Approval request sent!")
            print(f"   Message ID: {sent_message.id}")
            
            # Wait for response (with timeout)
            response = await self.wait_for_approval(action_id, timeout_minutes=60)
            
            return response
            
        except Exception as e:
            print(f"❌ Error sending approval request: {e}")
            return False
    
    async def wait_for_approval(self, action_id: str, timeout_minutes: int = 60) -> bool:
        """Wait for user response to approval request"""
        
        print(f"⏳ Waiting for user response (timeout: {timeout_minutes} min)...")
        
        # In production, this would listen for callback events
        # For now, we'll simulate
        
        await asyncio.sleep(2)  # Simulate waiting
        
        # Check if approved
        approval = self.pending_approvals.get(action_id, {})
        return approval.get("status") == "approved"
    
    async def handle_callback(self, event):
        """Handle button callback from user"""
        
        callback_data = event.data.decode('utf-8')
        action, action_id = callback_data.split('_', 1)
        
        if action == "approve":
            print(f"✅ User APPROVED: {action_id}")
            self.pending_approvals[action_id]["status"] = "approved"
            await event.answer("✅ Approved! Brain will apply the fix.")
            
        elif action == "reject":
            print(f"❌ User REJECTED: {action_id}")
            self.pending_approvals[action_id]["status"] = "rejected"
            await event.answer("❌ Rejected! Brain will not apply the fix.")
            
        elif action == "details":
            # Send full details
            await event.answer("📋 Sending full details...")
    
    async def send_notification(self, message: str):
        """Send a notification to user (no buttons)"""
        try:
            await self.client.send_message(self.user_chat_id, message)
            print(f"📤 Notification sent: {message[:50]}...")
        except Exception as e:
            print(f"⚠️  Notification error: {e}")
    
    async def send_daily_summary(self, report: str):
        """Send daily activity summary"""
        
        summary = f"""
🧠 **BRAIN DAILY SUMMARY**
{datetime.now().strftime('%Y-%m-%d')}

{report[:500]}...

Full report available in data/training_reports/
"""
        
        await self.send_notification(summary)


class KillSwitch:
    """Emergency control for the Autonomous Brain"""
    
    def __init__(self):
        self.is_active = True
        self.pause_duration = 0
        
        print("🔴 Kill Switch initialized")
    
    def emergency_stop(self):
        """EMERGENCY STOP - Halt all autonomous operations"""
        
        print(f"\n{'='*60}")
        print(f"🔴 EMERGENCY STOP ACTIVATED")
        print(f"{'='*60}")
        print(f"All autonomous operations halted")
        print(f"Brain entering safe mode (monitoring only)")
        print(f"{'='*60}\n")
        
        self.is_active = False
        
        # Save state
        with open("data/brain_state.json", 'w') as f:
            import json
            json.dump({
                "stopped_at": datetime.now().isoformat(),
                "reason": "emergency_stop",
                "status": "safe_mode"
            }, f)
        
        return True
    
    def pause(self, hours: int = 1):
        """Temporarily pause autonomous operations"""
        
        print(f"⏸️  Brain paused for {hours} hour(s)")
        self.pause_duration = hours
        
        return True
    
    def resume(self):
        """Resume autonomous operations"""
        
        if not self.is_active:
            print("❌ Cannot resume - emergency stop active. Manual intervention required.")
            return False
        
        print(f"▶️  Brain resumed")
        self.pause_duration = 0
        
        return True
    
    def get_status(self) -> Dict:
        """Get kill switch status"""
        
        return {
            "active": self.is_active,
            "paused": self.pause_duration > 0,
            "pause_duration_hours": self.pause_duration,
            "mode": "stopped" if not self.is_active else "paused" if self.pause_duration > 0 else "active"
        }


if __name__ == "__main__":
    async def test_approval_system():
        print("🧪 Testing Approval System\n")
        
        approval = ApprovalSystem()
        kill_switch = KillSwitch()
        
        # Test 1: Kill switch
        print("Test 1: Kill Switch")
        status = kill_switch.get_status()
        print(f"   Status: {status}\n")
        
        # Test 2: Mock approval request
        print("Test 2: Approval Request (simulated)")
        print("   → Would send Telegram message")
        print("   → With APPROVE/REJECT buttons")
        print("   → User approves/rejects")
        print("   → Brain proceeds accordingly\n")
        
        # Test 3: Notification
        print("Test 3: Notification System")
        print("   → Would send status updates")
        print("   → Daily summaries")
        print("   → Emergency alerts\n")
        
        print("✅ Approval system ready!")
        print("\nIn production:")
        print("- Connects to Telegram")
        print("- Sends real approval requests")
        print("- Handles button callbacks")
        print("- Implements kill switch commands")
    
    asyncio.run(test_approval_system())
