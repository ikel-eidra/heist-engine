#!/usr/bin/env python3
"""
HEIST ENGINE - MODULE 1: THE EAR
Social Sentiment Aggregator & Alpha Hunter

Purpose: Monitor 20+ channels across Telegram, Discord, and X/Twitter
         to detect token launch signals and calculate hype scores.

Engineer: MANE_25-10-20
Project: Operation First Blood
"""

import asyncio
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import json

# External imports (will be installed via requirements.txt)
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Message
except ImportError:
    TelegramClient = None
    
try:
    import discord
    from discord.ext import commands
except ImportError:
    discord = None

try:
    import tweepy
except ImportError:
    tweepy = None

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ============================================
# CONFIGURATION
# ============================================

class EarConfig:
    """Configuration for The Ear module"""
    
    # Telegram settings
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE')
    
    # Discord settings
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    # Twitter/X settings
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
    TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_SECRET')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    
    # Operational settings
    SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL_SECONDS', '5'))
    MIN_HYPE_SCORE = int(os.getenv('MIN_HYPE_SCORE', '70'))
    
    # Target channels (from Chimera's intelligence)
    TELEGRAM_CHANNELS = [
        '@wolfxsignals',
        '@CryptoPumpClub',
        '@BinanceKillers',
        '@FatPigSignals',
        '@WallstreetQueenOfficial',
        '@EveningTrader',
        '@CryptoNinjasTrading',
        '@Dash2Trade',
        '@SatoshiCalls',
        '@PhantomDegen',
        '@CryptoInsider',
        '@TonnyDrops',
    ]
    
    DISCORD_SERVERS = [
        'limbo',
        'ucsdegen',
        'raventrading',
        'coincodecap',
        'primetrading',
    ]
    
    TWITTER_ACCOUNTS = [
        'Degen_Callerz',
        'Defi_Warhol',
        'degenBRO__',
        'ShawnCT_',
        '0xHamadav',
        'zoomerfied',
        'DegenArchit3ct',
        'CrypttraderDave',
        'degenbams',
        'Eze_Wilberforce',
    ]
    
    # Hype keywords (weighted by importance)
    HYPE_KEYWORDS = {
        # Ultra high value keywords
        'launch': 10,
        'presale': 10,
        'stealth launch': 15,
        'fair launch': 12,
        
        # High value keywords
        'moon': 8,
        '100x': 10,
        '1000x': 12,
        'gem': 7,
        'alpha': 9,
        'call': 8,
        
        # Medium value keywords
        'pump': 6,
        'bullish': 5,
        'buy now': 7,
        'entry': 6,
        'degen': 5,
        
        # Contract indicators (very high value)
        'CA:': 15,
        'contract': 12,
        '0x': 10,  # Ethereum address
    }
    
    # Contract address patterns
    ETH_ADDRESS_PATTERN = r'0x[a-fA-F0-9]{40}'
    SOLANA_ADDRESS_PATTERN = r'[1-9A-HJ-NP-Za-km-z]{32,44}'


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class TokenSignal:
    """Represents a detected token signal"""
    token_name: Optional[str] = None
    contract_address: Optional[str] = None
    chain: Optional[str] = None  # 'ethereum', 'solana', 'bsc', etc.
    source_platform: str = ''  # 'telegram', 'discord', 'twitter'
    source_channel: str = ''
    message_text: str = ''
    timestamp: datetime = field(default_factory=datetime.now)
    hype_score: float = 0.0
    raw_data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'token_name': self.token_name,
            'contract_address': self.contract_address,
            'chain': self.chain,
            'source_platform': self.source_platform,
            'source_channel': self.source_channel,
            'message_text': self.message_text,
            'timestamp': self.timestamp.isoformat(),
            'hype_score': self.hype_score,
        }


@dataclass
class HypeMetrics:
    """Tracks hype metrics for a token over time"""
    contract_address: str
    message_count: int = 0
    total_hype_score: float = 0.0
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    sources: Set[str] = field(default_factory=set)
    
    @property
    def average_hype_score(self) -> float:
        """Calculate average hype score"""
        return self.total_hype_score / self.message_count if self.message_count > 0 else 0.0
    
    @property
    def velocity(self) -> float:
        """Calculate message velocity (messages per minute)"""
        time_diff = (self.last_seen - self.first_seen).total_seconds() / 60
        return self.message_count / time_diff if time_diff > 0 else 0.0


# ============================================
# THE EAR - MAIN CLASS
# ============================================

class TheEar:
    """
    The Ear: Social Sentiment Aggregator
    
    Monitors multiple platforms for token launch signals and calculates
    hype scores based on message frequency, keywords, and influencer activity.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('TheEar')
        self.config = EarConfig()
        
        # Tracking structures
        self.token_metrics: Dict[str, HypeMetrics] = {}
        self.recent_signals: List[TokenSignal] = []
        self.processed_message_ids: Set[str] = set()
        
        # Platform clients (initialized later)
        self.telegram_client: Optional[TelegramClient] = None
        self.discord_client: Optional[discord.Client] = None
        self.twitter_client: Optional[tweepy.Client] = None
        
        # State
        self.is_running = False
        
    # ============================================
    # INITIALIZATION
    # ============================================
    
    async def initialize(self):
        """Initialize all platform connections"""
        self.logger.info("🎧 Initializing The Ear...")
        
        await self._init_telegram()
        await self._init_discord()
        await self._init_twitter()
        
        self.logger.info("✅ The Ear is ready to listen")
        
    async def _init_telegram(self):
        """Initialize Telegram client"""
        if not TelegramClient:
            self.logger.warning("⚠️ Telethon not installed, Telegram monitoring disabled")
            return
            
        if not self.config.TELEGRAM_API_ID or not self.config.TELEGRAM_API_HASH:
            self.logger.warning("⚠️ Telegram credentials not configured")
            return
            
        try:
            self.telegram_client = TelegramClient(
                'heist_session',
                self.config.TELEGRAM_API_ID,
                self.config.TELEGRAM_API_HASH
            )
            await self.telegram_client.start(phone=self.config.TELEGRAM_PHONE)
            
            # Register message handler
            @self.telegram_client.on(events.NewMessage(chats=self.config.TELEGRAM_CHANNELS))
            async def telegram_message_handler(event):
                await self._process_telegram_message(event)
            
            self.logger.info(f"✅ Telegram connected, monitoring {len(self.config.TELEGRAM_CHANNELS)} channels")
            
        except Exception as e:
            self.logger.error(f"❌ Telegram initialization failed: {e}")
            
    async def _init_discord(self):
        """Initialize Discord client"""
        if not discord:
            self.logger.warning("⚠️ discord.py not installed, Discord monitoring disabled")
            return
            
        if not self.config.DISCORD_BOT_TOKEN:
            self.logger.warning("⚠️ Discord token not configured")
            return
            
        try:
            intents = discord.Intents.default()
            intents.message_content = True
            
            self.discord_client = discord.Client(intents=intents)
            
            @self.discord_client.event
            async def on_message(message):
                await self._process_discord_message(message)
            
            # Start Discord client in background
            asyncio.create_task(self.discord_client.start(self.config.DISCORD_BOT_TOKEN))
            
            self.logger.info(f"✅ Discord connected, monitoring {len(self.config.DISCORD_SERVERS)} servers")
            
        except Exception as e:
            self.logger.error(f"❌ Discord initialization failed: {e}")
            
    async def _init_twitter(self):
        """Initialize Twitter/X client"""
        if not tweepy:
            self.logger.warning("⚠️ Tweepy not installed, Twitter monitoring disabled")
            return
            
        if not self.config.TWITTER_BEARER_TOKEN:
            self.logger.warning("⚠️ Twitter credentials not configured")
            return
            
        try:
            self.twitter_client = tweepy.Client(
                bearer_token=self.config.TWITTER_BEARER_TOKEN,
                consumer_key=self.config.TWITTER_API_KEY,
                consumer_secret=self.config.TWITTER_API_SECRET,
                access_token=self.config.TWITTER_ACCESS_TOKEN,
                access_token_secret=self.config.TWITTER_ACCESS_SECRET,
            )
            
            self.logger.info(f"✅ Twitter connected, monitoring {len(self.config.TWITTER_ACCOUNTS)} accounts")
            
        except Exception as e:
            self.logger.error(f"❌ Twitter initialization failed: {e}")
    
    # ============================================
    # MESSAGE PROCESSING
    # ============================================
    
    async def _process_telegram_message(self, event):
        """Process incoming Telegram message"""
        try:
            message = event.message
            message_id = f"tg_{message.chat_id}_{message.id}"
            
            # Avoid duplicate processing
            if message_id in self.processed_message_ids:
                return
            self.processed_message_ids.add(message_id)
            
            # Extract signal
            signal = await self._extract_signal(
                text=message.text or '',
                platform='telegram',
                channel=event.chat.username or str(event.chat_id),
                message_id=message_id
            )
            
            if signal and signal.hype_score >= self.config.MIN_HYPE_SCORE:
                await self._handle_signal(signal)
                
        except Exception as e:
            self.logger.error(f"Error processing Telegram message: {e}")
    
    async def _process_discord_message(self, message):
        """Process incoming Discord message"""
        try:
            # Ignore bot messages
            if message.author.bot:
                return
                
            message_id = f"dc_{message.guild.id}_{message.id}"
            
            if message_id in self.processed_message_ids:
                return
            self.processed_message_ids.add(message_id)
            
            signal = await self._extract_signal(
                text=message.content,
                platform='discord',
                channel=message.guild.name if message.guild else 'DM',
                message_id=message_id
            )
            
            if signal and signal.hype_score >= self.config.MIN_HYPE_SCORE:
                await self._handle_signal(signal)
                
        except Exception as e:
            self.logger.error(f"Error processing Discord message: {e}")
    
    async def _extract_signal(self, text: str, platform: str, channel: str, message_id: str) -> Optional[TokenSignal]:
        """Extract token signal from message text"""
        
        # Calculate hype score
        hype_score = self._calculate_hype_score(text)
        
        # Extract contract addresses
        eth_addresses = re.findall(self.config.ETH_ADDRESS_PATTERN, text)
        sol_addresses = re.findall(self.config.SOLANA_ADDRESS_PATTERN, text)
        
        contract_address = None
        chain = None
        
        if eth_addresses:
            contract_address = eth_addresses[0]
            chain = 'ethereum'
        elif sol_addresses:
            contract_address = sol_addresses[0]
            chain = 'solana'
        
        # Only create signal if we have a contract address or high hype score
        if contract_address or hype_score >= self.config.MIN_HYPE_SCORE:
            signal = TokenSignal(
                contract_address=contract_address,
                chain=chain,
                source_platform=platform,
                source_channel=channel,
                message_text=text[:500],  # Truncate long messages
                hype_score=hype_score,
                raw_data={'message_id': message_id}
            )
            
            return signal
        
        return None
    
    def _calculate_hype_score(self, text: str) -> float:
        """Calculate hype score based on keywords and patterns"""
        score = 0.0
        text_lower = text.lower()
        
        # Check for hype keywords
        for keyword, weight in self.config.HYPE_KEYWORDS.items():
            if keyword.lower() in text_lower:
                score += weight
        
        # Bonus for multiple exclamation marks
        exclamation_count = text.count('!')
        score += min(exclamation_count * 2, 10)
        
        # Bonus for emojis (simple heuristic)
        emoji_count = sum(1 for char in text if ord(char) > 127000)
        score += min(emoji_count, 5)
        
        # Bonus for ALL CAPS words
        caps_words = sum(1 for word in text.split() if word.isupper() and len(word) > 2)
        score += min(caps_words * 3, 15)
        
        return score
    
    async def _handle_signal(self, signal: TokenSignal):
        """Handle a detected signal"""
        self.recent_signals.append(signal)
        
        # Update metrics if we have a contract address
        if signal.contract_address:
            if signal.contract_address not in self.token_metrics:
                self.token_metrics[signal.contract_address] = HypeMetrics(
                    contract_address=signal.contract_address
                )
            
            metrics = self.token_metrics[signal.contract_address]
            metrics.message_count += 1
            metrics.total_hype_score += signal.hype_score
            metrics.last_seen = datetime.now()
            metrics.sources.add(f"{signal.source_platform}:{signal.source_channel}")
        
        # Log the signal
        self.logger.info(
            f"🎯 SIGNAL DETECTED | Score: {signal.hype_score:.1f} | "
            f"Platform: {signal.source_platform} | "
            f"Channel: {signal.source_channel} | "
            f"Contract: {signal.contract_address or 'N/A'}"
        )
        
        # Emit signal to other modules (The Eye)
        await self._emit_signal(signal)
    
    async def _emit_signal(self, signal: TokenSignal):
        """Emit signal to other modules for processing"""
        # This will be implemented as an event system or message queue
        # For now, we'll just store it
        pass
    
    # ============================================
    # PUBLIC API
    # ============================================
    
    async def start(self):
        """Start listening to all platforms"""
        self.is_running = True
        self.logger.info("🎧 The Ear is now listening...")
        
        # Keep running
        while self.is_running:
            await asyncio.sleep(self.config.SCAN_INTERVAL)
            
            # Periodic cleanup of old data
            await self._cleanup_old_data()
    
    async def stop(self):
        """Stop listening"""
        self.is_running = False
        
        if self.telegram_client:
            await self.telegram_client.disconnect()
        
        if self.discord_client:
            await self.discord_client.close()
        
        self.logger.info("🔇 The Ear has stopped listening")
    
    async def _cleanup_old_data(self):
        """Clean up old signals and metrics"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Remove old signals
        self.recent_signals = [
            s for s in self.recent_signals 
            if s.timestamp > cutoff_time
        ]
        
        # Remove old metrics
        self.token_metrics = {
            addr: metrics 
            for addr, metrics in self.token_metrics.items()
            if metrics.last_seen > cutoff_time
        }
    
    def get_top_signals(self, limit: int = 10) -> List[TokenSignal]:
        """Get top signals by hype score"""
        return sorted(
            self.recent_signals,
            key=lambda s: s.hype_score,
            reverse=True
        )[:limit]
    
    def get_token_metrics(self, contract_address: str) -> Optional[HypeMetrics]:
        """Get metrics for a specific token"""
        return self.token_metrics.get(contract_address)


# ============================================
# MAIN EXECUTION
# ============================================

async def main():
    """Main execution function for testing"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    
    # Create and initialize The Ear
    ear = TheEar()
    await ear.initialize()
    
    # Start listening
    try:
        await ear.start()
    except KeyboardInterrupt:
        await ear.stop()


if __name__ == '__main__':
    asyncio.run(main())

