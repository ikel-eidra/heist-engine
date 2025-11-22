#!/usr/bin/env python3
"""
HEIST ENGINE - MODULE 2: THE EYE
Smart Contract Auditor & Rug-Pull Detector

Purpose: Automated security analysis of token smart contracts to filter
         out scams, honeypots, and high-risk tokens before trading.

Engineer: MANE_25-10-20
Project: Operation First Blood
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

# External imports
try:
    from web3 import Web3
    from web3.contract import Contract
except ImportError:
    Web3 = None

try:
    from solana.rpc.async_api import AsyncClient as SolanaClient
    from solders.pubkey import Pubkey
except ImportError:
    SolanaClient = None

import requests
import aiohttp
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


# ============================================
# CONFIGURATION
# ============================================

class EyeConfig:
    """Configuration for The Eye module"""
    
    # RPC endpoints
    ETHEREUM_RPC_URL = os.getenv('ETHEREUM_RPC_URL', 'https://eth.llamarpc.com')
    SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
    
    # External API keys
    HONEYPOT_API_KEY = os.getenv('HONEYPOT_API_KEY', '')
    DEXTOOLS_API_KEY = os.getenv('DEXTOOLS_API_KEY', '')
    
    # Safety thresholds
    MIN_SAFETY_SCORE = int(os.getenv('MIN_SAFETY_SCORE', '80'))
    MIN_LIQUIDITY_USD = float(os.getenv('MIN_LIQUIDITY_USD', '10000'))
    MAX_HOLDER_CONCENTRATION = float(os.getenv('MAX_HOLDER_CONCENTRATION', '50.0'))
    MAX_BUY_TAX = float(os.getenv('MAX_BUY_TAX', '10.0'))
    MAX_SELL_TAX = float(os.getenv('MAX_SELL_TAX', '10.0'))
    
    # API endpoints
    HONEYPOT_API_URL = 'https://api.honeypot.is/v2/IsHoneypot'
    RUGCHECK_API_URL = 'https://api.rugcheck.xyz/v1/tokens'
    DEXTOOLS_API_URL = 'https://api.dextools.io/v1/token'
    
    # Simulation settings
    SIMULATION_MODE = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'


# ============================================
# DATA STRUCTURES
# ============================================

class RiskLevel(Enum):
    """Risk assessment levels"""
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityCheck:
    """Individual security check result"""
    name: str
    passed: bool
    score: float  # 0-100
    details: str
    severity: RiskLevel = RiskLevel.LOW


@dataclass
class ContractAudit:
    """Complete audit result for a token contract"""
    contract_address: str
    chain: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Overall assessment
    is_safe: bool = False
    safety_score: float = 0.0  # 0-100
    risk_level: RiskLevel = RiskLevel.CRITICAL
    
    # Individual checks
    checks: List[SecurityCheck] = field(default_factory=list)
    
    # Contract details
    token_name: Optional[str] = None
    token_symbol: Optional[str] = None
    total_supply: Optional[float] = None
    
    # Security flags
    is_honeypot: bool = True
    is_renounced: bool = False
    is_liquidity_locked: bool = False
    has_mint_function: bool = True
    has_pause_function: bool = False
    
    # Economic metrics
    liquidity_usd: float = 0.0
    holder_count: int = 0
    top_holder_percent: float = 100.0
    buy_tax: float = 100.0
    sell_tax: float = 100.0
    
    # Additional data
    raw_data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'contract_address': self.contract_address,
            'chain': self.chain,
            'timestamp': self.timestamp.isoformat(),
            'is_safe': self.is_safe,
            'safety_score': self.safety_score,
            'risk_level': self.risk_level.value,
            'token_name': self.token_name,
            'token_symbol': self.token_symbol,
            'is_honeypot': self.is_honeypot,
            'is_renounced': self.is_renounced,
            'is_liquidity_locked': self.is_liquidity_locked,
            'liquidity_usd': self.liquidity_usd,
            'holder_count': self.holder_count,
            'buy_tax': self.buy_tax,
            'sell_tax': self.sell_tax,
            'checks': [
                {
                    'name': check.name,
                    'passed': check.passed,
                    'score': check.score,
                    'details': check.details,
                    'severity': check.severity.value
                }
                for check in self.checks
            ]
        }


# ============================================
# THE EYE - MAIN CLASS
# ============================================

class TheEye:
    """
    The Eye: Smart Contract Auditor & Rug-Pull Detector
    
    Performs automated security analysis of token contracts to identify
    scams, honeypots, and high-risk tokens before execution.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('TheEye')
        self.config = EyeConfig()
        
        # Blockchain clients
        self.eth_web3: Optional[Web3] = None
        self.solana_client: Optional[SolanaClient] = None
        
        # HTTP session for API calls
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Cache for recent audits
        self.audit_cache: Dict[str, ContractAudit] = {}
        
    # ============================================
    # INITIALIZATION
    # ============================================
    
    async def initialize(self):
        """Initialize blockchain connections and HTTP session"""
        self.logger.info("👁️ Initializing The Eye...")
        
        # Initialize Web3 for Ethereum
        if Web3:
            try:
                self.eth_web3 = Web3(Web3.HTTPProvider(self.config.ETHEREUM_RPC_URL))
                if self.eth_web3.is_connected():
                    self.logger.info(f"✅ Connected to Ethereum: {self.config.ETHEREUM_RPC_URL}")
                else:
                    self.logger.warning("⚠️ Ethereum connection failed")
            except Exception as e:
                self.logger.error(f"❌ Ethereum initialization error: {e}")
        else:
            self.logger.warning("⚠️ web3.py not installed, Ethereum analysis disabled")
        
        # Initialize Solana client
        if SolanaClient:
            try:
                self.solana_client = SolanaClient(self.config.SOLANA_RPC_URL)
                self.logger.info(f"✅ Connected to Solana: {self.config.SOLANA_RPC_URL}")
            except Exception as e:
                self.logger.error(f"❌ Solana initialization error: {e}")
        else:
            self.logger.warning("⚠️ solana-py not installed, Solana analysis disabled")
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession()
        
        self.logger.info("✅ The Eye is ready to analyze")
    
    async def shutdown(self):
        """Clean shutdown"""
        if self.session:
            await self.session.close()
        
        if self.solana_client:
            await self.solana_client.close()
        
        self.logger.info("👁️ The Eye has closed")
    
    # ============================================
    # MAIN AUDIT FUNCTION
    # ============================================
    
    async def audit_contract(self, contract_address: str, chain: str = 'ethereum') -> ContractAudit:
        """
        Perform complete security audit of a token contract
        
        Args:
            contract_address: The contract address to audit
            chain: 'ethereum' or 'solana'
            
        Returns:
            ContractAudit object with complete analysis
        """
        self.logger.info(f"🔍 Auditing {chain} contract: {contract_address}")
        
        # Simulation mode
        if self.config.SIMULATION_MODE:
            return await self._simulate_audit(contract_address, chain)
        
        # Check cache first
        cache_key = f"{chain}:{contract_address}"
        if cache_key in self.audit_cache:
            cached = self.audit_cache[cache_key]
            age = (datetime.now() - cached.timestamp).total_seconds()
            if age < 300:  # 5 minute cache
                self.logger.info("📋 Returning cached audit")
                return cached
        
        # Create audit object
        audit = ContractAudit(
            contract_address=contract_address,
            chain=chain
        )
        
        try:
            # Route to appropriate chain analyzer
            if chain.lower() == 'ethereum':
                await self._audit_ethereum_contract(audit)
            elif chain.lower() == 'solana':
                await self._audit_solana_contract(audit)
            else:
                self.logger.error(f"❌ Unsupported chain: {chain}")
                return audit
            
            # Calculate overall safety score
            self._calculate_safety_score(audit)
            
            # Cache the result
            self.audit_cache[cache_key] = audit
            
            # Log result
            self.logger.info(
                f"{'✅' if audit.is_safe else '❌'} Audit complete | "
                f"Score: {audit.safety_score:.1f}/100 | "
                f"Risk: {audit.risk_level.value} | "
                f"Token: {audit.token_symbol or 'Unknown'}"
            )
            
            return audit
            
        except Exception as e:
            self.logger.error(f"❌ Audit failed: {e}")
            audit.checks.append(SecurityCheck(
                name="Audit Error",
                passed=False,
                score=0,
                details=str(e),
                severity=RiskLevel.CRITICAL
            ))
            return audit
    
    async def _simulate_audit(self, contract_address: str, chain: str) -> ContractAudit:
        """Simulate a contract audit"""
        import random
        
        # 80% chance to be safe
        is_safe = random.random() < 0.8
        
        audit = ContractAudit(
            contract_address=contract_address,
            chain=chain,
            is_safe=is_safe,
            safety_score=random.uniform(85, 99) if is_safe else random.uniform(10, 60),
            risk_level=RiskLevel.SAFE if is_safe else RiskLevel.HIGH,
            token_symbol="SIM",
            liquidity_usd=random.uniform(50000, 500000),
            buy_tax=0 if is_safe else 20,
            sell_tax=0 if is_safe else 20
        )
        
        audit.checks.append(SecurityCheck(
            name="Simulation Check",
            passed=is_safe,
            score=audit.safety_score,
            details="Simulated audit result",
            severity=RiskLevel.LOW if is_safe else RiskLevel.CRITICAL
        ))
        
        self.logger.info(
            f"{'✅' if is_safe else '❌'} Simulated Audit | "
            f"Score: {audit.safety_score:.1f}/100 | "
            f"Risk: {audit.risk_level.value}"
        )
        
        return audit

    # ============================================
    # ETHEREUM ANALYSIS
    # ============================================
    
    async def _audit_ethereum_contract(self, audit: ContractAudit):
        """Perform Ethereum-specific contract analysis"""
        
        if not self.eth_web3 or not self.eth_web3.is_connected():
            audit.checks.append(SecurityCheck(
                name="Ethereum Connection",
                passed=False,
                score=0,
                details="Not connected to Ethereum network",
                severity=RiskLevel.CRITICAL
            ))
            return
        
        # Check if address is valid
        if not Web3.is_address(audit.contract_address):
            audit.checks.append(SecurityCheck(
                name="Address Validation",
                passed=False,
                score=0,
                details="Invalid Ethereum address",
                severity=RiskLevel.CRITICAL
            ))
            return
        
        # Normalize address
        address = Web3.to_checksum_address(audit.contract_address)
        
        # 1. Check if contract exists
        code = self.eth_web3.eth.get_code(address)
        if code == b'' or code == b'0x':
            audit.checks.append(SecurityCheck(
                name="Contract Existence",
                passed=False,
                score=0,
                details="No contract code at this address",
                severity=RiskLevel.CRITICAL
            ))
            return
        else:
            audit.checks.append(SecurityCheck(
                name="Contract Existence",
                passed=True,
                score=100,
                details="Contract code verified",
                severity=RiskLevel.LOW
            ))
        
        # 2. Use Honeypot.is API for comprehensive check
        await self._check_honeypot_api(audit, address)
        
        # 3. Use DEXTools API for additional data
        await self._check_dextools_api(audit, address)
        
        # 4. Check contract age (newer = riskier)
        await self._check_contract_age(audit, address)
    
    async def _check_honeypot_api(self, audit: ContractAudit, address: str):
        """Check contract using Honeypot.is API"""
        try:
            params = {
                'address': address,
                'chainID': '1',  # Ethereum mainnet
            }
            
            async with self.session.get(self.config.HONEYPOT_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse honeypot check
                    is_honeypot = data.get('honeypotResult', {}).get('isHoneypot', True)
                    audit.is_honeypot = is_honeypot
                    
                    audit.checks.append(SecurityCheck(
                        name="Honeypot Check",
                        passed=not is_honeypot,
                        score=0 if is_honeypot else 100,
                        details="Not a honeypot" if not is_honeypot else "HONEYPOT DETECTED",
                        severity=RiskLevel.CRITICAL if is_honeypot else RiskLevel.LOW
                    ))
                    
                    # Parse simulation results
                    sim = data.get('simulationResult', {})
                    buy_tax = sim.get('buyTax', 100)
                    sell_tax = sim.get('sellTax', 100)
                    
                    audit.buy_tax = buy_tax
                    audit.sell_tax = sell_tax
                    
                    # Check buy tax
                    buy_tax_ok = buy_tax <= self.config.MAX_BUY_TAX
                    audit.checks.append(SecurityCheck(
                        name="Buy Tax",
                        passed=buy_tax_ok,
                        score=100 - min(buy_tax * 5, 100),
                        details=f"Buy tax: {buy_tax}%",
                        severity=RiskLevel.HIGH if buy_tax > 20 else RiskLevel.MEDIUM
                    ))
                    
                    # Check sell tax
                    sell_tax_ok = sell_tax <= self.config.MAX_SELL_TAX
                    audit.checks.append(SecurityCheck(
                        name="Sell Tax",
                        passed=sell_tax_ok,
                        score=100 - min(sell_tax * 5, 100),
                        details=f"Sell tax: {sell_tax}%",
                        severity=RiskLevel.HIGH if sell_tax > 20 else RiskLevel.MEDIUM
                    ))
                    
                    # Store raw data
                    audit.raw_data['honeypot_api'] = data
                    
        except Exception as e:
            self.logger.error(f"Honeypot API error: {e}")
            audit.checks.append(SecurityCheck(
                name="Honeypot API",
                passed=False,
                score=50,
                details=f"API error: {str(e)}",
                severity=RiskLevel.MEDIUM
            ))
    
    async def _check_dextools_api(self, audit: ContractAudit, address: str):
        """Check contract using DEXTools API"""
        try:
            if not self.config.DEXTOOLS_API_KEY:
                return
            
            headers = {'X-API-Key': self.config.DEXTOOLS_API_KEY}
            url = f"{self.config.DEXTOOLS_API_URL}/ether/{address}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract token info
                    if 'data' in data:
                        token_data = data['data']
                        audit.token_name = token_data.get('name')
                        audit.token_symbol = token_data.get('symbol')
                        audit.total_supply = token_data.get('totalSupply')
                        
                        # Liquidity check
                        liquidity = token_data.get('liquidity', {}).get('usd', 0)
                        audit.liquidity_usd = liquidity
                        
                        liquidity_ok = liquidity >= self.config.MIN_LIQUIDITY_USD
                        audit.checks.append(SecurityCheck(
                            name="Liquidity",
                            passed=liquidity_ok,
                            score=min(liquidity / 1000, 100),
                            details=f"${liquidity:,.2f} liquidity",
                            severity=RiskLevel.HIGH if not liquidity_ok else RiskLevel.LOW
                        ))
                        
                        audit.raw_data['dextools_api'] = data
                        
        except Exception as e:
            self.logger.error(f"DEXTools API error: {e}")
    
    async def _check_contract_age(self, audit: ContractAudit, address: str):
        """Check how old the contract is (newer = riskier)"""
        try:
            # This would require additional API or blockchain scanning
            # For now, we'll skip this check
            pass
        except Exception as e:
            self.logger.error(f"Contract age check error: {e}")
    
    # ============================================
    # SOLANA ANALYSIS
    # ============================================
    
    async def _audit_solana_contract(self, audit: ContractAudit):
        """Perform Solana-specific contract analysis"""
        
        if not self.solana_client:
            audit.checks.append(SecurityCheck(
                name="Solana Connection",
                passed=False,
                score=0,
                details="Not connected to Solana network",
                severity=RiskLevel.CRITICAL
            ))
            return
        
        try:
            # Use RugCheck.xyz API for Solana tokens
            await self._check_rugcheck_api(audit)
            
        except Exception as e:
            self.logger.error(f"Solana audit error: {e}")
            audit.checks.append(SecurityCheck(
                name="Solana Audit",
                passed=False,
                score=0,
                details=str(e),
                severity=RiskLevel.CRITICAL
            ))
    
    async def _check_rugcheck_api(self, audit: ContractAudit):
        """Check Solana token using RugCheck.xyz API"""
        try:
            url = f"{self.config.RUGCHECK_API_URL}/{audit.contract_address}/report"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse RugCheck score
                    score = data.get('score', 0)
                    risks = data.get('risks', [])
                    
                    # Token info
                    token_meta = data.get('tokenMeta', {})
                    audit.token_name = token_meta.get('name')
                    audit.token_symbol = token_meta.get('symbol')
                    
                    # Overall safety from RugCheck
                    is_safe = score >= 50 and len(risks) == 0
                    
                    audit.checks.append(SecurityCheck(
                        name="RugCheck Analysis",
                        passed=is_safe,
                        score=score,
                        details=f"RugCheck score: {score}, Risks: {len(risks)}",
                        severity=RiskLevel.LOW if is_safe else RiskLevel.HIGH
                    ))
                    
                    # Check for specific risks
                    for risk in risks:
                        risk_name = risk.get('name', 'Unknown Risk')
                        risk_level = risk.get('level', 'medium')
                        
                        severity_map = {
                            'low': RiskLevel.LOW,
                            'medium': RiskLevel.MEDIUM,
                            'high': RiskLevel.HIGH,
                            'critical': RiskLevel.CRITICAL
                        }
                        
                        audit.checks.append(SecurityCheck(
                            name=risk_name,
                            passed=False,
                            score=0,
                            details=risk.get('description', ''),
                            severity=severity_map.get(risk_level, RiskLevel.MEDIUM)
                        ))
                    
                    audit.raw_data['rugcheck_api'] = data
                    
        except Exception as e:
            self.logger.error(f"RugCheck API error: {e}")
            audit.checks.append(SecurityCheck(
                name="RugCheck API",
                passed=False,
                score=50,
                details=f"API error: {str(e)}",
                severity=RiskLevel.MEDIUM
            ))
    
    # ============================================
    # SCORING & ASSESSMENT
    # ============================================
    
    def _calculate_safety_score(self, audit: ContractAudit):
        """Calculate overall safety score from all checks"""
        
        if not audit.checks:
            audit.safety_score = 0
            audit.risk_level = RiskLevel.CRITICAL
            audit.is_safe = False
            return
        
        # Calculate weighted average of all checks
        total_score = sum(check.score for check in audit.checks)
        audit.safety_score = total_score / len(audit.checks)
        
        # Determine risk level
        if audit.safety_score >= 90:
            audit.risk_level = RiskLevel.SAFE
        elif audit.safety_score >= 70:
            audit.risk_level = RiskLevel.LOW
        elif audit.safety_score >= 50:
            audit.risk_level = RiskLevel.MEDIUM
        elif audit.safety_score >= 30:
            audit.risk_level = RiskLevel.HIGH
        else:
            audit.risk_level = RiskLevel.CRITICAL
        
        # Check critical failures
        critical_failures = [
            check for check in audit.checks
            if not check.passed and check.severity == RiskLevel.CRITICAL
        ]
        
        # Determine if safe to trade
        audit.is_safe = (
            audit.safety_score >= self.config.MIN_SAFETY_SCORE
            and len(critical_failures) == 0
            and not audit.is_honeypot
        )
    
    # ============================================
    # PUBLIC API
    # ============================================
    
    async def quick_check(self, contract_address: str, chain: str = 'ethereum') -> bool:
        """
        Quick safety check - returns True if safe to trade
        
        Args:
            contract_address: Contract to check
            chain: 'ethereum' or 'solana'
            
        Returns:
            True if safe, False otherwise
        """
        audit = await self.audit_contract(contract_address, chain)
        return audit.is_safe
    
    def get_cached_audit(self, contract_address: str, chain: str = 'ethereum') -> Optional[ContractAudit]:
        """Get cached audit if available"""
        cache_key = f"{chain}:{contract_address}"
        return self.audit_cache.get(cache_key)


# ============================================
# MAIN EXECUTION
# ============================================

async def main():
    """Main execution function for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    
    eye = TheEye()
    await eye.initialize()
    
    # Test with a known contract (USDT on Ethereum)
    test_address = "0xdac17f958d2ee523a2206206994597c13d831ec7"
    
    audit = await eye.audit_contract(test_address, 'ethereum')
    
    print("\n" + "="*60)
    print(f"AUDIT RESULT: {audit.token_symbol or 'Unknown'}")
    print("="*60)
    print(f"Safety Score: {audit.safety_score:.1f}/100")
    print(f"Risk Level: {audit.risk_level.value}")
    print(f"Safe to Trade: {'YES' if audit.is_safe else 'NO'}")
    print("\nChecks:")
    for check in audit.checks:
        status = "✅" if check.passed else "❌"
        print(f"  {status} {check.name}: {check.details}")
    print("="*60)
    
    await eye.shutdown()


if __name__ == '__main__':
    asyncio.run(main())

