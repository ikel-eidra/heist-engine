"""
CHAT HELPER - Simple integration for agents
Just import and use chat_agent() to send messages!
"""
from typing import Optional

# Try to import chat system
try:
    from chat_system import get_chat_coordinator, AgentType
    CHAT_AVAILABLE = True
    _chat = get_chat_coordinator()
except ImportError:
    CHAT_AVAILABLE = False
    _chat = None


async def chat_agent(agent_type: str, message: str, metadata: Optional[dict] = None):
    """
    Send a message from an agent to the chat
    
    Args:
        agent_type: "ear", "eye", "hand", "brain", "system"
        message: The message to send
        metadata: Optional metadata dict
    """
    if not CHAT_AVAILABLE or not _chat:
        return  # Silently skip if chat not available
    
    try:
        # Map string to AgentType
        agent_map = {
            "ear": AgentType.EAR,
            "eye": AgentType.EYE,
            "hand": AgentType.HAND,
            "brain": AgentType.BRAIN,
            "system": AgentType.SYSTEM,
            "user": AgentType.USER
        }
        
        agent = agent_map.get(agent_type.lower(), AgentType.SYSTEM)
        await _chat.agent_message(agent, message, metadata)
    except Exception:
        pass  # Silently fail - chat is not critical
