#!/usr/bin/env python3
"""
Daily Training System
=====================

Brain's continuous learning module.
Researches crypto markets, AI updates, and security best practices daily.
"""

import asyncio
import os
from datetime import datetime, time
from typing import Dict, List
import requests
from groq import Groq


class TrainingScheduler:
    """Schedules and runs daily training sessions"""
    
    def __init__(self, training_time: str = "23:00", duration_minutes: int = 60):
        """
        Args:
            training_time: Time to run training (HH:MM format, 24h)
            duration_minutes: Duration of training session
        """
        self.training_time = training_time
        self.duration_minutes = duration_minutes
        self.researcher = ResearchAgent()
        
        print(f"📚 Training Scheduler initialized")
        print(f"   Daily training: {training_time} ({duration_minutes} min)")
    
    async def run_daily_training(self):
        """Run a complete training session"""
        
        print(f"\n{'='*60}")
        print(f"🧠 DAILY TRAINING SESSION - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}\n")
        
        topics = [
            "crypto_market_trends",
            "new_signal_channels",
            "ai_model_updates",
            "security_vulnerabilities",
            "trading_strategies"
        ]
        
        insights = {}
        
        for topic in topics:
            print(f"📖 Researching: {topic}...")
            topic_insights = await self.researcher.research_topic(topic)
            insights[topic] = topic_insights
            print(f"   ✅ Found {len(topic_insights)} insights\n")
        
        # Generate training report
        report = await self.generate_training_report(insights)
        
        # Save report
        self.save_training_report(report)
        
        print(f"\n{'='*60}")
        print(f"✅ TRAINING SESSION COMPLETE")
        print(f"{'='*60}\n")
        
        return report
    
    async def generate_training_report(self, insights: Dict) -> str:
        """Generate human-readable training report"""
        
        report = f"""
# 🧠 BRAIN TRAINING REPORT
**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Duration:** {self.duration_minutes} minutes

## Summary
Brain completed daily training and learned from {len(insights)} research topics.

"""
        
        for topic, topic_insights in insights.items():
            report += f"\n## {topic.replace('_', ' ').title()}\n"
            for insight in topic_insights[:3]:  # Top 3 per topic
                report += f"- {insight}\n"
        
        report += "\n## Recommendations\n"
        report += "Based on today's research, Brain recommends:\n"
        report += "- Monitoring emerging trends\n"
        report += "- Testing new signal sources\n"
        report += "- Updating security protocols\n"
        
        return report
    
    def save_training_report(self, report: str):
        """Save training report to file"""
        import os
        from pathlib import Path
        
        reports_dir = Path("data/training_reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{datetime.now().strftime('%Y-%m-%d')}.md"
        filepath = reports_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        print(f"💾 Report saved: {filepath}")


class ResearchAgent:
    """Conducts internet research for training"""
    
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.coingecko_api = "https://api.coingecko.com/api/v3"
    
    async def research_topic(self, topic: str) -> List[str]:
        """Research a specific topic"""
        
        if topic == "crypto_market_trends":
            return await self.research_crypto_markets()
        elif topic == "new_signal_channels":
            return await self.discover_telegram_channels()
        elif topic == "ai_model_updates":
            return await self.check_ai_updates()
        elif topic == "security_vulnerabilities":
            return await self.research_security()
        elif topic == "trading_strategies":
            return await self.research_strategies()
        else:
            return []
    
    async def research_crypto_markets(self) -> List[str]:
        """Research current crypto market trends"""
        
        try:
            # Get top coins from CoinGecko
            response = requests.get(
                f"{self.coingecko_api}/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 10,
                    "page": 1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                coins = response.json()
                
                insights = []
                for coin in coins[:5]:
                    change_24h = coin.get('price_change_percentage_24h', 0)
                    trend = "📈" if change_24h > 0 else "📉"
                    insights.append(
                        f"{trend} {coin['name']}: {change_24h:+.2f}% (24h), "
                        f"Vol: ${coin.get('total_volume', 0):,.0f}"
                    )
                
                return insights
            
        except Exception as e:
            print(f"⚠️  Market research error: {e}")
        
        return ["Market data unavailable"]
    
    async def discover_telegram_channels(self) -> List[str]:
        """Discover potential signal channels"""
        
        # Use AI to suggest channels based on criteria
        prompt = """You are a crypto trading bot discovering signal channels.

Suggest 5 popular, legitimate Telegram channels for crypto trading signals.
Consider:
- High follower count
- Active posting
- Good reputation
- Free or reasonable pricing

Return ONLY channel names (with @), one per line."""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            channels = response.choices[0].message.content.strip().split('\n')
            return [ch.strip() for ch in channels if ch.strip().startswith('@')]
            
        except Exception as e:
            print(f"⚠️  Channel discovery error: {e}")
            return []
    
    async def check_ai_updates(self) -> List[str]:
        """Check for AI/Groq model updates"""
        
        # Use AI to research itself
        prompt = """What are the latest updates to Groq AI and Llama models?
List 3-5 key improvements or new features released recently.
Be specific and concise."""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500
            )
            
            updates = response.choices[0].message.content.strip().split('\n')
            return [u.strip() for u in updates if u.strip() and not u.strip().startswith('#')][:5]
            
        except Exception as e:
            print(f"⚠️  AI updates check error: {e}")
            return ["AI updates check unavailable"]
    
    async def research_security(self) -> List[str]:
        """Research security best practices"""
        
        prompt = """List 5 critical security practices for crypto trading bots.
Focus on:
- API key management
- Wallet security
- Code vulnerabilities
- Network security

Be specific and actionable."""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            practices = response.choices[0].message.content.strip().split('\n')
            return [p.strip() for p in practices if p.strip() and not p.strip().startswith('#')][:5]
            
        except Exception as e:
            print(f"⚠️  Security research error: {e}")
            return ["Security research unavailable"]
    
    async def research_strategies(self) -> List[str]:
        """Research trading strategies"""
        
        prompt = """Suggest 5 proven cryptocurrency trading strategies.
Focus on:
- Risk management
- Entry/exit strategies
- Signal validation
- Position sizing

Be specific and practical."""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=600
            )
            
            strategies = response.choices[0].message.content.strip().split('\n')
            return [s.strip() for s in strategies if s.strip() and not s.strip().startswith('#')][:5]
            
        except Exception as e:
            print(f"⚠️  Strategy research error: {e}")
            return ["Strategy research unavailable"]


if __name__ == "__main__":
    async def test_training():
        scheduler = TrainingScheduler()
        
        print("🧪 Testing Daily Training System\n")
        
        report = await scheduler.run_daily_training()
        
        print("\n📄 TRAINING REPORT:")
        print(report)
    
    asyncio.run(test_training())
