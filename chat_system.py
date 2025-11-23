"""
MULTI-AGENT CHAT SYSTEM
Enables real-time communication between user and all AI agents
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging


class AgentType(Enum):
    """Types of agents in the system"""
    USER = "user"
    BRAIN = "brain"
    EAR = "ear"
    EYE = "eye"
    HAND = "hand"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """A message in the chat"""
    agent: str  # Agent type as string
    message: str
    timestamp: str
    metadata: Optional[Dict] = None
    
    def to_dict(self):
        return {
            "agent": self.agent,
            "message": self.message,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {}
        }


class ChatCoordinator:
    """
    Coordinates chat between user and all AI agents
    Manages WebSocket connections and message routing
    """
    
    def __init__(self, logger=None):
        self.logger = logger or self._setup_logger()
        
        # Active WebSocket connections
        self.connections: Set = set()
        
        # Message history (last N messages)
        self.max_history = 100
        self.message_history: List[ChatMessage] = []
        
        # Registered agents (for routing user commands)
        self.agents: Dict[str, any] = {}
        
        self.enabled = True
        self.logger.info("💬 Chat Coordinator initialized")
    
    def _setup_logger(self):
        """Setup basic logger if none provided"""
        logger = logging.getLogger("ChatCoordinator")
        logger.setLevel(logging.INFO)
        return logger
    
    async def register_agent(self, agent_type: AgentType, agent_instance):
        """Register an agent to participate in chat"""
        self.agents[agent_type.value] = agent_instance
        self.logger.info(f"💬 Registered agent: {agent_type.value}")
        
        # Announce to chat
        await self.broadcast_system_message(
            f"Agent {agent_type.value.upper()} is now online"
        )
    
    async def connect(self, websocket):
        """Register a new WebSocket connection"""
        self.connections.add(websocket)
        self.logger.info(f"💬 New connection. Total: {len(self.connections)}")
        
        # Send recent message history to new connection
        for msg in self.message_history[-20:]:  # Last 20 messages
            await websocket.send_text(json.dumps(msg.to_dict()))
        
        # Welcome message
        await self.send_to_connection(
            websocket,
            ChatMessage(
                agent=AgentType.SYSTEM.value,
                message="Welcome to Heist Engine Command Center! 🚀",
                timestamp=datetime.now().isoformat()
            )
        )
    
    async def disconnect(self, websocket):
        """Remove a WebSocket connection"""
        self.connections.discard(websocket)
        self.logger.info(f"💬 Connection closed. Total: {len(self.connections)}")
    
    async def send_to_connection(self, websocket, message: ChatMessage):
        """Send message to a specific connection"""
        try:
            await websocket.send_text(json.dumps(message.to_dict()))
        except Exception as e:
            self.logger.error(f"Error sending to connection: {e}")
            self.connections.discard(websocket)
    
    async def broadcast(self, message: ChatMessage):
        """Send message to all connected clients"""
        if not self.enabled:
            return
        
        # Add to history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]
        
        # Send to all connections
        disconnected = set()
        for connection in self.connections:
            try:
                await connection.send_text(json.dumps(message.to_dict()))
            except Exception as e:
                self.logger.error(f"Error broadcasting: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected
        self.connections -= disconnected
    
    async def broadcast_system_message(self, message: str):
        """Broadcast a system message"""
        await self.broadcast(ChatMessage(
            agent=AgentType.SYSTEM.value,
            message=message,
            timestamp=datetime.now().isoformat()
        ))
    
    async def agent_message(self, agent_type: AgentType, message: str, metadata: Dict = None):
        """Send a message from an agent"""
        await self.broadcast(ChatMessage(
            agent=agent_type.value,
            message=message,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        ))
    
    async def handle_user_message(self, message: str) -> str:
        """
        Handle a message from the user
        Route to appropriate agent or broadcast
        """
        message_lower = message.lower()
        
        # Special commands
        if message_lower in ["status", "status?", "what's happening?"]:
            return await self._get_status_report()
        
        if "help" in message_lower:
            return self._get_help_message()
        
        # Route to specific agent if mentioned
        if "brain" in message_lower and "brain" in self.agents:
            return f"🧠 Brain: I hear you! Let me analyze that..."
        
        if any(word in message_lower for word in ["signal", "ear", "listening"]):
            return "🎧 Ear: Monitoring channels for signals..."
        
        if any(word in message_lower for word in ["audit", "eye", "contract", "safe"]):
            return "👁️ Eye: Standing by for contract audits..."
        
        if any(word in message_lower for word in ["trade", "hand", "execute", "buy", "sell"]):
            return "✋ Hand: Ready to execute when given the signal..."
        
        # Default response
        return "💬 Message received! Agents are working on your request."
    
    async def _get_status_report(self) -> str:
        """Get status from all agents"""
        report = []
        report.append("📊 **SYSTEM STATUS**")
        report.append("")
        
        # Get status from each agent if available
        if "brain" in self.agents:
            report.append("🧠 **Brain:** Ready for analysis")
        
        if "ear" in self.agents:
            report.append("🎧 **Ear:** Listening to channels")
        
        if "eye" in self.agents:
            report.append("👁️ **Eye:** Ready to audit contracts")
        
        if "hand" in self.agents:
            report.append("✋ **Hand:** Standing by for trades")
        
        report.append("")
        report.append(f"💬 **Chat:** {len(self.connections)} active connection(s)")
        
        return "\n".join(report)
    
    def _get_help_message(self) -> str:
        """Get help message with available commands"""
        return """💡 **Available Commands:**

• `status` - Get status from all agents
• `help` - Show this message
• Mention agent names (brain, ear, eye, hand) to interact
• Ask questions naturally - agents will respond!

**Examples:**
• "Why did you skip that signal?"
• "What's the current market status?"
• "Show me open positions"
"""


# Global chat coordinator instance
chat_coordinator = None


def get_chat_coordinator(logger=None) -> ChatCoordinator:
    """Get or create global chat coordinator"""
    global chat_coordinator
    if chat_coordinator is None:
        chat_coordinator = ChatCoordinator(logger=logger)
    return chat_coordinator
