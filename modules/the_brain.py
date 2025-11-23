"""
THE BRAIN - AI Decision Engine for Heist Engine
Uses Groq API (Llama 3.1 70B) to make intelligent trading decisions
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
import asyncio

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  WARNING: groq package not installed. AI features disabled.")
    print("   Install with: pip install groq")


@dataclass
class AIDecision:
    """AI trading decision"""
    action: str  # "BUY", "SKIP", "WAIT"
    confidence: float  # 0.0 to 1.0
    position_size: float  # % of portfolio to allocate
    reasoning: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class TradingMemory:
    """Stores and retrieves past trading decisions and outcomes"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.history: List[Dict] = []
        
    def add_decision(self, signal: Dict, decision: AIDecision, outcome: Optional[Dict] = None):
        """Store a decision and its outcome"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "signal": signal,
            "decision": {
                "action": decision.action,
                "confidence": decision.confidence,
                "position_size": decision.position_size,
                "reasoning": decision.reasoning
            },
            "outcome": outcome
        }
        
        self.history.append(entry)
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_similar_signals(self, token_symbol: str, limit: int = 5) -> List[Dict]:
        """Get past decisions for similar tokens"""
        similar = [
            entry for entry in self.history
            if entry["signal"].get("token_symbol") == token_symbol
        ]
        return similar[-limit:] if similar else []
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        completed = [e for e in self.history if e.get("outcome")]
        if not completed:
            return 0.0
        
        wins = sum(1 for e in completed if e["outcome"].get("pnl", 0) > 0)
        return wins / len(completed) if completed else 0.0


class TheBrain:
    """AI-Powered Trading Decision Engine"""
    
    def __init__(self, logger=None):
        self.logger = logger or self._setup_logger()
        
        # Groq API setup
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.enabled = GROQ_AVAILABLE and bool(self.groq_api_key)
        
        if self.enabled:
            self.client = AsyncGroq(api_key=self.groq_api_key)
            self.model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
            self.logger.info(f"🧠 The Brain initialized with {self.model}")
        else:
            self.logger.warning("🧠 The Brain disabled - missing Groq API key or package")
        
        # Memory system
        self.memory = TradingMemory()
        
        # Configuration
        self.min_confidence = float(os.getenv("AI_MIN_CONFIDENCE", "0.70"))
        self.max_position_size = float(os.getenv("AI_MAX_POSITION", "0.10"))  # 10% max
    
    def _setup_logger(self):
        """Setup basic logger if none provided"""
        import logging
        logger = logging.getLogger("TheBrain")
        logger.setLevel(logging.INFO)
        return logger
    
    async def analyze_signal(
        self, 
        signal: Dict, 
        audit: Dict, 
        market_context: Optional[Dict] = None
    ) -> AIDecision:
        """
        Analyze a trading signal and make a decision
        
        Args:
            signal: Token signal data from The Ear
            audit: Contract audit results from The Eye
            market_context: Current market conditions (optional)
        
        Returns:
            AIDecision with action, confidence, and reasoning
        """
        if not self.enabled:
            # Fallback to algorithm-based decision
            return self._fallback_decision(signal, audit)
        
        try:
            # Build analysis prompt
            prompt = self._build_prompt(signal, audit, market_context)
            
            # Get AI decision
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower = more focused
                max_tokens=500
            )
            
            # Parse AI response
            ai_text = response.choices[0].message.content
            decision = self._parse_ai_response(ai_text)
            
            self.logger.info(
                f"🧠 AI Decision: {decision.action} "
                f"(confidence: {decision.confidence:.2f}) - {decision.reasoning[:50]}..."
            )
            
            return decision
            
        except Exception as e:
            self.logger.error(f"🧠 AI analysis failed: {e}")
            return self._fallback_decision(signal, audit)
    
    def _get_system_prompt(self) -> str:
        """System prompt that defines the AI's role"""
        success_rate = self.memory.get_success_rate()
        
        return f"""You are an expert crypto trading AI with a {success_rate*100:.1f}% historical success rate.

Your job is to analyze trading signals and decide whether to BUY, SKIP, or WAIT.

Consider these factors:
1. **Contract Safety**: Is the contract safe? Any red flags?
2. **Signal Strength**: How strong is the hype/momentum?
3. **Risk/Reward**: Is the potential profit worth the risk?
4. **Market Context**: Current market conditions
5. **Historical Patterns**: Similar trades in the past

Respond in this EXACT format:
ACTION: [BUY/SKIP/WAIT]
CONFIDENCE: [0.00-1.00]
POSITION_SIZE: [0.00-0.10]
REASONING: [Your analysis in 1-2 sentences]

Be conservative - only recommend BUY for high-conviction opportunities."""
    
    def _build_prompt(
        self, 
        signal: Dict, 
        audit: Dict, 
        market_context: Optional[Dict]
    ) -> str:
        """Build the analysis prompt"""
        
        # Get similar past signals
        similar = self.memory.get_similar_signals(signal.get("token_symbol", ""), limit=3)
        past_performance = ""
        if similar:
            wins = sum(1 for s in similar if s.get("outcome", {}).get("pnl", 0) > 0)
            past_performance = f"\n**Past Performance for {signal.get('token_symbol')}:** {wins}/{len(similar)} wins"
        
        prompt = f"""Analyze this trading signal:

**SIGNAL DATA:**
- Token: {signal.get('token_symbol', 'UNKNOWN')}
- Chain: {signal.get('chain', 'UNKNOWN')}
- Source: {signal.get('source_platform', 'UNKNOWN')} / {signal.get('source_channel', 'UNKNOWN')}
- Hype Score: {signal.get('hype_score', 0):.1f}/100
- Message: {signal.get('message_text', '')[:200]}

**CONTRACT AUDIT:**
- Safe: {audit.get('is_safe', False)}
- Safety Score: {audit.get('safety_score', 0):.1f}/100
- Risk Level: {audit.get('risk_level', 'UNKNOWN')}
- Liquidity: ${audit.get('liquidity_usd', 0):,.0f}
- Buy Tax: {audit.get('buy_tax', 0)}% | Sell Tax: {audit.get('sell_tax', 0)}%
- Red Flags: {len(audit.get('checks', []))} checks, {sum(1 for c in audit.get('checks', []) if not c.get('passed', True))} failed
{past_performance}

**MARKET CONTEXT:**
{json.dumps(market_context, indent=2) if market_context else 'Not available'}

Should we trade this signal?"""
        
        return prompt
    
    def _parse_ai_response(self, ai_text: str) -> AIDecision:
        """Parse AI response into AIDecision"""
        try:
            lines = ai_text.strip().split('\n')
            action = "SKIP"
            confidence = 0.0
            position_size = 0.0
            reasoning = "Unable to parse AI response"
            
            for line in lines:
                line = line.strip()
                if line.startswith("ACTION:"):
                    action = line.split(":", 1)[1].strip().upper()
                elif line.startswith("CONFIDENCE:"):
                    confidence = float(line.split(":", 1)[1].strip())
                elif line.startswith("POSITION_SIZE:") or line.startswith("POSITION SIZE:"):
                    position_size = float(line.split(":", 1)[1].strip())
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()
            
            # Validate and cap values
            confidence = max(0.0, min(1.0, confidence))
            position_size = max(0.0, min(self.max_position_size, position_size))
            
            # Validate action
            if action not in ["BUY", "SKIP", "WAIT"]:
                action = "SKIP"
            
            return AIDecision(
                action=action,
                confidence=confidence,
                position_size=position_size,
                reasoning=reasoning
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            return AIDecision(
                action="SKIP",
                confidence=0.0,
                position_size=0.0,
                reasoning="Error parsing AI response"
            )
    
    def _fallback_decision(self, signal: Dict, audit: Dict) -> AIDecision:
        """Fallback algorithm-based decision when AI is unavailable"""
        is_safe = audit.get("is_safe", False)
        safety_score = audit.get("safety_score", 0)
        hype_score = signal.get("hype_score", 0)
        
        # Simple algorithm logic
        if is_safe and safety_score >= 70 and hype_score >= 75:
            return AIDecision(
                action="BUY",
                confidence=0.60,
                position_size=0.03,
                reasoning="Algorithm: Safe contract + high hype"
            )
        else:
            return AIDecision(
                action="SKIP",
                confidence=0.80,
                position_size=0.0,
                reasoning="Algorithm: Failed safety or hype threshold"
            )
    
    async def learn_from_outcome(
        self,
        signal: Dict,
        decision: AIDecision,
        outcome: Dict
    ):
        """Store trade outcome for learning"""
        self.memory.add_decision(signal, decision, outcome)
        
        pnl = outcome.get("pnl", 0)
        result = "WIN" if pnl > 0 else "LOSS"
        
        self.logger.info(
            f"🧠 Learning: {signal.get('token_symbol')} = {result} "
           f"(PnL: {pnl:+.1f}%, Success Rate: {self.memory.get_success_rate()*100:.1f}%)"
        )
