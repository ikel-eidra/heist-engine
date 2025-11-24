#!/usr/bin/env python3
"""
Adaptive Position Sizing System
================================

Intelligent position sizing that:
1. Supports multiple strategies (conservative/balanced/aggressive)
2. Compounds profits automatically
3. Adapts based on performance
4. Implements comprehensive risk controls
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict
import logging


class PositionSizingStrategy(Enum):
    """Position sizing strategies"""
    CONSERVATIVE = "conservative"  # 5% per trade, low risk
    BALANCED = "balanced"          # 15% per trade, medium risk
    AGGRESSIVE = "aggressive"      # 30% per trade, high risk (scalper)
    ADAPTIVE = "adaptive"          # Adjusts based on performance


@dataclass
class RiskLimits:
    """Risk management limits"""
    max_position_size_percent: float
    max_open_positions: int
    stop_loss_percent: float
    take_profit_percent: float
    daily_loss_limit_percent: float
    max_trades_per_day: int
    min_trade_usd: float
    max_trade_usd: float


class AdaptivePositionSizer:
    """
    Intelligent position sizing with compounding and risk management
    """
    
    def __init__(self, strategy: PositionSizingStrategy = PositionSizingStrategy.BALANCED):
        self.logger = logging.getLogger('PositionSizer')
        self.strategy = strategy
        
        # Performance tracking
        self.total_trades = 0
        self.winning_streak = 0
        self.losing_streak = 0
        self.daily_pnl_percent = 0.0
        self.trades_today = 0
        
        # Get risk limits for strategy
        self.risk_limits = self._get_risk_limits(strategy)
        
        self.logger.info(f"📊 Position Sizer initialized - Strategy: {strategy.value}")
    
    def _get_risk_limits(self, strategy: PositionSizingStrategy) -> RiskLimits:
        """Get risk limits for each strategy"""
        
        if strategy == PositionSizingStrategy.CONSERVATIVE:
            return RiskLimits(
                max_position_size_percent=0.05,  # 5% per trade
                max_open_positions=5,             # Can have 5 positions (25% max)
                stop_loss_percent=0.02,           # -2% stop loss
                take_profit_percent=0.05,         # +5% take profit
                daily_loss_limit_percent=0.05,    # -5% daily limit
                max_trades_per_day=15,            # Max 15 trades/day
                min_trade_usd=5.0,
                max_trade_usd=5000.0
            )
        
        elif strategy == PositionSizingStrategy.BALANCED:
            return RiskLimits(
                max_position_size_percent=0.15,  # 15% per trade
                max_open_positions=4,             # Can have 4 positions (60% max)
                stop_loss_percent=0.025,          # -2.5% stop loss
                take_profit_percent=0.04,         # +4% take profit
                daily_loss_limit_percent=0.08,    # -8% daily limit
                max_trades_per_day=12,            # Max 12 trades/day
                min_trade_usd=5.0,
                max_trade_usd=10000.0
            )
        
        elif strategy == PositionSizingStrategy.AGGRESSIVE:
            return RiskLimits(
                max_position_size_percent=0.30,  # 30% per trade (SCALPER!)
                max_open_positions=3,             # Can have 3 positions (90% max)
                stop_loss_percent=0.03,           # -3% stop loss
                take_profit_percent=0.02,         # +2% take profit (quick scalps)
                daily_loss_limit_percent=0.10,    # -10% daily limit
                max_trades_per_day=10,            # Max 10 trades/day
                min_trade_usd=5.0,
                max_trade_usd=20000.0
            )
        
        elif strategy == PositionSizingStrategy.ADAPTIVE:
            # Starts balanced, adjusts based on performance
            return self._get_risk_limits(PositionSizingStrategy.BALANCED)
    
    def calculate_position_size(
        self, 
        wallet_balance_usd: float,
        current_open_positions: int = 0
    ) -> Optional[float]:
        """
        Calculate optimal position size
        
        Args:
            wallet_balance_usd: Current wallet balance
            current_open_positions: Number of positions currently open
            
        Returns:
            Position size in USD, or None if no trade should be taken
        """
        
        # Check if we can trade
        if not self._can_trade(current_open_positions):
            return None
        
        # Get base position size from strategy
        base_percent = self.risk_limits.max_position_size_percent
        
        # Apply adaptive adjustments if using adaptive strategy
        if self.strategy == PositionSizingStrategy.ADAPTIVE:
            base_percent = self._get_adaptive_percent()
        
        # Calculate position size
        position_size = wallet_balance_usd * base_percent
        
        # Apply min/max limits
        position_size = max(
            self.risk_limits.min_trade_usd,
            min(position_size, self.risk_limits.max_trade_usd)
        )
        
        # Reduce size if we have open positions (risk management)
        if current_open_positions > 0:
            reduction_factor = 1.0 - (0.1 * current_open_positions)  # -10% per position
            position_size *= max(0.5, reduction_factor)  # Never below 50%
        
        self.logger.info(
            f"💰 Position Size: ${position_size:.2f} "
            f"({base_percent*100:.1f}% of ${wallet_balance_usd:.2f})"
        )
        
        return position_size
    
    def _can_trade(self, current_open_positions: int) -> bool:
        """Check if we can open a new trade"""
        
        # Check position limit
        if current_open_positions >= self.risk_limits.max_open_positions:
            self.logger.warning(
                f"⚠️ Max positions reached ({self.risk_limits.max_open_positions})"
            )
            return False
        
        # Check daily trade limit
        if self.trades_today >= self.risk_limits.max_trades_per_day:
            self.logger.warning(
                f"⚠️ Daily trade limit reached ({self.risk_limits.max_trades_per_day})"
            )
            return False
        
        # Check daily loss limit
        if self.daily_pnl_percent <= -self.risk_limits.daily_loss_limit_percent:
            self.logger.warning(
                f"🛑 Daily loss limit hit ({self.daily_pnl_percent:.2%})"
            )
            return False
        
        # Check losing streak (emergency brake)
        if self.losing_streak >= 5:
            self.logger.warning(
                f"⚠️ Losing streak too long ({self.losing_streak}), pausing"
            )
            return False
        
        return True
    
    def _get_adaptive_percent(self) -> float:
        """Calculate adaptive position size based on performance"""
        
        # Start with balanced (15%)
        base_percent = 0.15
        
        # Increase on winning streak (up to aggressive 30%)
        if self.winning_streak >= 3:
            bonus = min(0.15, self.winning_streak * 0.03)  # +3% per win, max +15%
            base_percent += bonus
            self.logger.info(f"📈 Increasing size due to streak: +{bonus*100:.0f}%")
        
        # Decrease on losing streak (down to conservative 5%)
        elif self.losing_streak >= 2:
            penalty = min(0.10, self.losing_streak * 0.05)  # -5% per loss, max -10%
            base_percent -= penalty
            self.logger.info(f"📉 Reducing size due to losses: -{penalty*100:.0f}%")
        
        # Decrease if near daily loss limit
        loss_proximity = abs(self.daily_pnl_percent) / self.risk_limits.daily_loss_limit_percent
        if loss_proximity > 0.5:  # If we've lost >50% of daily limit
            base_percent *= (1 - loss_proximity * 0.3)  # Reduce up to 30%
            self.logger.info(f"⚠️ Near daily limit, reducing size")
        
        # Clamp between 5% and 30%
        return max(0.05, min(0.30, base_percent))
    
    def record_trade_result(self, profit_percent: float):
        """Record trade result for adaptive sizing"""
        
        self.total_trades += 1
        self.trades_today += 1
        self.daily_pnl_percent += profit_percent
        
        if profit_percent > 0:
            self.winning_streak += 1
            self.losing_streak = 0
            self.logger.info(f"✅ Win #{self.winning_streak}")
        else:
            self.losing_streak += 1
            self.winning_streak = 0
            self.logger.info(f"❌ Loss #{self.losing_streak}")
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at midnight)"""
        self.logger.info(
            f"📊 Daily stats: {self.trades_today} trades, "
            f"P&L: {self.daily_pnl_percent:+.2%}"
        )
        
        self.trades_today = 0
        self.daily_pnl_percent = 0.0
    
    def get_stop_loss_percent(self) -> float:
        """Get stop loss percentage for current strategy"""
        return self.risk_limits.stop_loss_percent
    
    def get_take_profit_percent(self) -> float:
        """Get take profit percentage for current strategy"""
        return self.risk_limits.take_profit_percent
    
    def get_status(self) -> Dict:
        """Get current sizer status"""
        return {
            "strategy": self.strategy.value,
            "position_size_percent": self.risk_limits.max_position_size_percent,
            "max_positions": self.risk_limits.max_open_positions,
            "stop_loss": self.risk_limits.stop_loss_percent,
            "take_profit": self.risk_limits.take_profit_percent,
            "trades_today": self.trades_today,
            "daily_pnl_percent": self.daily_pnl_percent,
            "winning_streak": self.winning_streak,
            "losing_streak": self.losing_streak,
            "can_trade": self._can_trade(0)
        }


if __name__ == "__main__":
    # Test all strategies
    print("🧪 Testing Position Sizing Strategies\n")
    
    strategies = [
        PositionSizingStrategy.CONSERVATIVE,
        PositionSizingStrategy.BALANCED,
        PositionSizingStrategy.AGGRESSIVE
    ]
    
    wallet = 1000.0
    
    for strategy in strategies:
        print(f"\n{'='*60}")
        print(f"📊 Strategy: {strategy.value.upper()}")
        print(f"{'='*60}")
        
        sizer = AdaptivePositionSizer(strategy)
        
        # Calculate position sizes
        pos_size = sizer.calculate_position_size(wallet, 0)
        print(f"Wallet: ${wallet:.2f}")
        print(f"Position Size: ${pos_size:.2f}")
        print(f"Stop Loss: {sizer.get_stop_loss_percent():.1%}")
        print(f"Take Profit: {sizer.get_take_profit_percent():.1%}")
        print(f"Max Positions: {sizer.risk_limits.max_open_positions}")
        print(f"Daily Limit: {sizer.risk_limits.daily_loss_limit_percent:.1%}")
    
    # Test adaptive
    print(f"\n{'='*60}")
    print(f"📊 Strategy: ADAPTIVE (with winning streak)")
    print(f"{'='*60}")
    
    sizer = AdaptivePositionSizer(PositionSizingStrategy.ADAPTIVE)
    
    print("\nSimulating 3 wins in a row:")
    for i in range(3):
        sizer.record_trade_result(0.02)  # +2% profit
    
    pos_size = sizer.calculate_position_size(wallet, 0)
    print(f"Position Size after streak: ${pos_size:.2f}")
    print(f"Status: {sizer.get_status()}")
    
    print("\n✅ All strategies tested!")
