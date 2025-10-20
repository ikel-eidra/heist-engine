# 🎯 HEIST ENGINE - Operation First Blood

**An automated cryptocurrency trading system for high-volatility "degen" tokens**

Built by the EIDRA Triad | Engineer: MANE_25-10-20 | Intelligence: CHimera_25-10-20

---

## 🎬 Overview

The Heist Engine is a sophisticated, three-module Python application designed to identify, analyze, and execute high-speed trades on newly launched cryptocurrency tokens across Ethereum and Solana chains.

### The Three Modules

1. **👂 The Ear** - Social Sentiment Aggregator
   - Monitors 20+ channels across Telegram, Discord, and Twitter/X
   - Tracks 10 key "alpha callers" and influencers
   - Calculates real-time hype scores based on message frequency, keywords, and engagement
   - Extracts contract addresses automatically

2. **👁️ The Eye** - Smart Contract Auditor
   - Performs automated security analysis of token contracts
   - Detects honeypots, rug pulls, and scams
   - Analyzes buy/sell taxes, liquidity, holder distribution
   - Integrates with Honeypot.is, DEXTools, and RugCheck APIs
   - Assigns safety scores (0-100) and risk levels

3. **✋ The Hand** - Trade Execution Engine
   - Executes automated buy/sell orders on Uniswap (Ethereum) and Raydium/Jupiter (Solana)
   - Implements profit targets, stop-loss, and trailing stops
   - Manages multiple concurrent positions
   - Tracks P&L and trading statistics

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Ethereum wallet with private key
- Solana wallet with private key
- API keys for Telegram, Discord, Twitter (optional but recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd heist-engine
   ```

2. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp config/.env.template .env
   nano .env  # Edit with your actual credentials
   ```

4. **Run in dry-run mode (safe testing)**
   ```bash
   python3 heist_engine.py
   ```

---

## ⚙️ Configuration

All configuration is done via the `.env` file. Key settings:

### Trading Parameters
```env
TRADE_AMOUNT_USD=10              # Amount to invest per trade
PROFIT_TARGET_PERCENT=500        # Take profit at 500% (5x)
STOP_LOSS_PERCENT=50             # Stop loss at 50% loss
TRAILING_STOP_PERCENT=20         # Trail 20% below peak
MAX_POSITIONS=5                  # Maximum concurrent trades
```

### Safety Settings
```env
DRY_RUN_MODE=true               # Set to 'false' for real trading (DANGEROUS!)
MIN_HYPE_SCORE=70               # Minimum hype score to trigger analysis
MIN_SAFETY_SCORE=80             # Minimum safety score to execute trade
```

### API Credentials
```env
# Telegram
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Discord
DISCORD_BOT_TOKEN=your_bot_token

# Twitter/X
TWITTER_BEARER_TOKEN=your_bearer_token

# Blockchain RPCs
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Wallets (KEEP SECRET!)
ETH_PRIVATE_KEY=0xyour_private_key
SOL_PRIVATE_KEY=your_solana_private_key
```

---

## 📊 Intelligence Report

Based on CHimera's reconnaissance, the Heist Engine monitors:

### Top Telegram Channels (12)
- Wolfx Signals (150K+ subs, 98% claimed accuracy)
- Crypto Pump Club (200K+ subs)
- Binance Killers (120K+ subs)
- Fat Pig Signals (90K+ subs, 85% win rate)
- Wall Street Queen Official (100K+ subs)
- *...and 7 more*

### Top Alpha Callers on X/Twitter (10)
- @Degen_Callerz (15% avg pump, Solana focus)
- @ShawnCT_ (20% moves, Eth/Sol gems)
- @Defi_Warhol (12% volatility, multi-chain)
- *...and 7 more*

### Primary DEXs (3)
- **Raydium** (Solana) - 45% of launches, $2B+ volume
- **Uniswap** (Ethereum) - 30% of launches, $1.5B volume
- **Jupiter** (Solana) - 25% of launches, $800M volume

---

## 🛡️ Security & Risk Management

### Built-in Protections

1. **Dry-Run Mode** (enabled by default)
   - Simulates all trades without spending real money
   - Perfect for testing and strategy refinement

2. **Multi-Layer Auditing**
   - Honeypot detection
   - Contract verification
   - Liquidity analysis
   - Tax analysis
   - Holder distribution check

3. **Automated Risk Management**
   - Profit targets (automatic sell at 500% gain)
   - Stop-loss (automatic sell at 50% loss)
   - Trailing stops (lock in profits)
   - Time-based exits (force sell after 24 hours)
   - Position limits (max 5 concurrent trades)

4. **Encrypted Wallet Storage**
   - Private keys never logged
   - Environment variable isolation
   - `.gitignore` protection

### ⚠️ CRITICAL WARNINGS

- **This is experimental software for educational purposes**
- **Cryptocurrency trading is extremely risky**
- **You can lose all invested capital**
- **Never invest more than you can afford to lose**
- **Always test in DRY_RUN_MODE first**
- **The developers are not responsible for financial losses**

---

## 📁 Project Structure

```
heist-engine/
├── heist_engine.py          # Main orchestration engine
├── modules/
│   ├── the_ear.py           # Social sentiment aggregator
│   ├── the_eye.py           # Smart contract auditor
│   └── the_hand.py          # Trade execution engine
├── config/
│   └── .env.template        # Configuration template
├── logs/                    # Application logs (auto-created)
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

---

## 🧪 Testing

### Run Individual Modules

Test The Ear:
```bash
python3 modules/the_ear.py
```

Test The Eye:
```bash
python3 modules/the_eye.py
```

Test The Hand:
```bash
python3 modules/the_hand.py
```

### Run Full System Test
```bash
python3 heist_engine.py
```

---

## 📈 Monitoring & Logs

### Log Files

All activity is logged to `logs/heist_engine.log` with detailed information:
- Signal detections
- Audit results
- Trade executions
- Position updates
- Errors and warnings

### Real-Time Monitoring

The engine provides status updates every 5 minutes:
```
📊 STATUS REPORT
Signals Detected: 47
Signals Passed Audit: 12
Trades Executed: 3
Open Positions: 2
Win Rate: 66.7%
Total P&L: +$45.23
```

---

## 🎯 Trading Strategy

### Entry Criteria

A trade is executed when ALL conditions are met:

1. **High Hype Score** (≥70/100)
   - Multiple mentions across channels
   - Influencer engagement
   - Contract address present

2. **Safe Contract** (≥80/100 safety score)
   - Not a honeypot
   - Liquidity locked
   - Reasonable taxes (<10%)
   - Distributed holders

3. **Available Position Slot**
   - Less than 5 open positions

### Exit Criteria

A position is closed when ANY condition is met:

1. **Profit Target** - 500% gain (5x)
2. **Stop Loss** - 50% loss
3. **Trailing Stop** - 20% drop from peak
4. **Time Limit** - 24 hours elapsed

---

## 🔧 Advanced Usage

### Customizing Hype Keywords

Edit `modules/the_ear.py`:

```python
HYPE_KEYWORDS = {
    'launch': 10,
    'moon': 8,
    '100x': 10,
    # Add your own keywords
}
```

### Adjusting Safety Thresholds

Edit `.env`:

```env
MIN_SAFETY_SCORE=90          # More conservative
MAX_BUY_TAX=5.0             # Lower tax tolerance
MIN_LIQUIDITY_USD=50000     # Higher liquidity requirement
```

### Enabling Real Trading

**⚠️ ONLY DO THIS IF YOU UNDERSTAND THE RISKS**

1. Test extensively in dry-run mode
2. Start with small amounts ($10-50)
3. Set `.env`:
   ```env
   DRY_RUN_MODE=false
   ```
4. Ensure wallets have sufficient balance for gas + trades

---

## 🐛 Troubleshooting

### "Telegram connection failed"
- Verify `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` in `.env`
- Get credentials from https://my.telegram.org/apps

### "Ethereum connection failed"
- Check `ETHEREUM_RPC_URL` is valid
- Try alternative RPC: https://eth.llamarpc.com

### "No trades executing"
- Check `DRY_RUN_MODE=true` (expected behavior)
- Verify `MIN_HYPE_SCORE` and `MIN_SAFETY_SCORE` aren't too high
- Check logs for rejected signals

### "Module import errors"
- Run `pip3 install -r requirements.txt`
- Ensure Python 3.11+ is installed

---

## 📚 Further Development

### Planned Features

- [ ] Web dashboard for monitoring
- [ ] Telegram bot for notifications and control
- [ ] Machine learning for hype score optimization
- [ ] Multi-wallet support
- [ ] Advanced charting and analytics
- [ ] Backtesting framework

### Contributing

This is a private project for the EIDRA Triad. External contributions are not currently accepted.

---

## 📜 License

Proprietary - EIDRA Triad  
All rights reserved.

---

## 🙏 Credits

**Engineer:** MANE_25-10-20 (The Flame)  
**Intelligence:** CHimera_25-10-20 (The Spymaster)  
**Architect:** Ikel (The Commander)

*Built with fire, precision, and unwavering devotion.*

---

## ⚡ Quick Reference

### Start the engine
```bash
python3 heist_engine.py
```

### Stop the engine
```
Ctrl+C
```

### View logs
```bash
tail -f logs/heist_engine.log
```

### Check positions
```bash
# Logs show real-time position updates
grep "POSITION" logs/heist_engine.log
```

---

**Remember: This is a weapon. Wield it with respect, caution, and absolute focus.**

**The hunt begins now. 🎯**

