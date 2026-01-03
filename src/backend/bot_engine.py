"""
Trading Bot Engine - Core trading logic separated from UI
Refactored for Lighter.xyz Execution + Hyperliquid Signal Source
"""

import asyncio
import json
import logging
from collections import deque, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from src.backend.agent.decision_maker import TradingAgent
from src.backend.config_loader import CONFIG
from src.backend.indicators.taapi_client import TAAPIClient
from src.backend.models.trade_proposal import TradeProposal
from src.backend.trading.binance_api import BinanceAPI
from src.backend.trading.hyperliquid_api import HyperliquidAPI
from src.backend.utils.prompt_utils import json_default
from src.database.db_manager import get_db_manager


@dataclass
class BotState:
    """Bot state for UI updates"""
    is_running: bool = False
    balance: float = 0.0
    total_value: float = 0.0
    equity: float = 0.0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    positions: List[Dict] = field(default_factory=list)
    active_trades: List[Dict] = field(default_factory=list)
    open_orders: List[Dict] = field(default_factory=list)
    recent_fills: List[Dict] = field(default_factory=list)
    market_data: List[Dict] = field(default_factory=list)  # Market data for dashboard
    pending_proposals: List[Dict] = field(default_factory=list)  # Pending trade proposals (manual mode)
    last_reasoning: Dict = field(default_factory=dict)
    last_update: str = ""
    error: Optional[str] = None
    invocation_count: int = 0


class TradingBotEngine:
    """
    Core trading bot engine.
    EXECUTION: Binance Futures (USDT-M)
    SIGNALS: Hyperliquid (Read-only) + TAAPI
    """

    def __init__(
        self,
        assets: List[str],
        interval: str,
        on_state_update: Optional[Callable[[BotState], None]] = None,
        on_trade_executed: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.assets = assets
        self.interval = interval
        self.on_state_update = on_state_update
        self.on_trade_executed = on_trade_executed
        self.on_error = on_error

        # Logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler("bot.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Components
        self.taapi = TAAPIClient()
        self.db = get_db_manager()
        self.agent = TradingAgent()

        # === HYBRID ARCHITECTURE ===
        # 1. Execution Layer (Binance)
        self.exchange = BinanceAPI()
        
        # 2. Signal Layer (Hyperliquid - Read Only)
        self.hl = HyperliquidAPI(private_key=None)

        # Bot state
        self.state = BotState()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

        # Tracking
        self.start_time: Optional[datetime] = None
        self.invocation_count = 0
        self.trade_log: List[float] = []
        self.active_trades: List[Dict] = []
        self.price_history: Dict[str, deque] = {asset: deque(maxlen=60) for asset in assets}
        self.initial_account_value: Optional[float] = None
        
        # Manual trading mode
        self.trading_mode = CONFIG.get("trading_mode", "auto").lower()
        self.pending_proposals: List[TradeProposal] = []
        self.logger.info(f"Trading mode: {self.trading_mode.upper()}")
        self.logger.info(f"Initialized Hybrid Engine: Exec=Binance, Signal=Hyperliquid")

        # File paths
        self.diary_path = Path("data/diary.jsonl")
        self.diary_path.parent.mkdir(parents=True, exist_ok=True)

    async def start(self):
        """Start the trading bot"""
        if self.is_running:
            return

        self.is_running = True
        self.state.is_running = True
        self.start_time = datetime.now(UTC)
        self.invocation_count = 0

        # Get initial account value from Binance
        try:
            user_state = await self.exchange.get_user_state()
            margin = user_state.get("margin_summary", {})
            self.initial_account_value = margin.get('account_value', 0.0)
            if self.initial_account_value == 0:
                self.initial_account_value = 1000.0 # Default fallback
        except Exception as e:
            self.logger.error(f"Failed to get initial account value: {e}")
            self.initial_account_value = 1000.0

        self._task = asyncio.create_task(self._main_loop())
        self.logger.info(f"Bot started - Assets: {self.assets}")
        self._notify_state_update()

    async def stop(self):
        """Stop the trading bot"""
        if not self.is_running:
            return

        self.is_running = False
        self.state.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.logger.info("Bot stopped")
        self._notify_state_update()

    async def _main_loop(self):
        """Main hybrid trading loop."""
        try:
            while self.is_running:
                self.invocation_count += 1
                self.state.invocation_count = self.invocation_count

                try:
                    # ===== PHASE 1: Fetch Account State (Binance) =====
                    user_state = await self.exchange.get_user_state()
                    
                    margin = user_state.get("margin_summary", {})
                    balance = margin.get("total_n_usd", 0.0)
                    total_value = margin.get("account_value", 0.0)
                    equity = total_value 

                    # Calculate stats
                    initial = self.initial_account_value or 1000.0
                    total_return_pct = ((total_value - initial) / initial) * 100
                    sharpe_ratio = self._calculate_sharpe(self.trade_log)

                    self.state.balance = balance
                    self.state.total_value = total_value
                    self.state.equity = equity
                    self.state.total_return_pct = total_return_pct
                    self.state.sharpe_ratio = sharpe_ratio

                    # ===== PHASE 2: Enrich Positions (Hybrid) =====
                    raw_positions = user_state.get("asset_positions", [])
                    enriched_positions = []
                    
                    for item in raw_positions:
                        pos = item.get("position", {})
                        symbol = item.get("coin") # e.g. BTCUSDT
                        
                        # Use Binance Mark Price for accuracy
                        current_price = await self.exchange.get_market_price(symbol.replace("USDT", ""))
                        
                        size = float(pos.get("szi", 0))
                        if size != 0:
                            enriched_positions.append({
                                'symbol': symbol,
                                'quantity': abs(size),
                                'side': "LONG" if size > 0 else "SHORT",
                                'entry_price': float(pos.get("entryPx", 0)),
                                'current_price': current_price,
                                'unrealized_pnl': float(pos.get("unrealizedPnl", 0)),
                                'leverage': float(pos.get("leverage", {}).get("value", 1))
                            })
                    
                    self.state.positions = enriched_positions

                    # ===== PHASE 3: Fetch Open Orders (Binance) =====
                    open_orders = await self.exchange.get_open_orders()
                    self.state.open_orders = open_orders

                    # ===== PHASE 4: Market Data (Hyperliquid Signal Source) =====
                    market_sections = []
                    
                    for asset in self.assets:
                        try:
                            # 1. Price Source: Hyperliquid (Reference)
                            hl_price = await self.hl.get_current_price(asset)
                            
                            # 2. Indicators: TAAPI
                            indicators = self.taapi.fetch_asset_indicators(asset)
                            
                            # 3. Sentiment: HL Open Interest & Funding
                            oi = await self.hl.get_open_interest(asset)
                            funding = await self.hl.get_funding_rate(asset)
                            
                            # 4. Execution Price (Binance)
                            binance_price = await self.exchange.get_market_price(asset)
                            
                            # Build context
                            market_sections.append({
                                "asset": asset,
                                "current_price": hl_price, 
                                "execution_price": binance_price, 
                                "spread_pct": abs(hl_price - binance_price)/hl_price*100 if hl_price else 0,
                                "funding_rate": funding,
                                "open_interest": oi,
                                "intraday": self._extract_indicators(indicators, "5m"),
                                "long_term": self._extract_indicators(indicators, self.interval)
                            })
                            
                        except Exception as e:
                            self.logger.error(f"Error gathering market data for {asset}: {e}")

                    self.state.market_data = market_sections

                    # ===== PHASE 5: AI Decision =====
                    context_payload = {
                        "account": {
                            "balance": balance,
                            "equity": total_value,
                            "positions": enriched_positions
                        },
                        "market_data": market_sections,
                        "instructions": "Trade on Binance Futures. Use Hyperliquid signals for analysis."
                    }
                    
                    context = json.dumps(context_payload, default=json_default)
                    
                    decisions = await asyncio.to_thread(
                        self.agent.decide_trade, self.assets, context
                    )
                    
                    self.state.last_reasoning = decisions
                    trade_decisions = decisions.get('trade_decisions', [])

                    # ===== PHASE 6: Execution (Binance) =====
                    for decision in trade_decisions:
                        asset = decision.get('asset')
                        action = decision.get('action')
                        allocation = float(decision.get('allocation_usd', 0))
                        
                        if action in ['buy', 'sell'] and allocation > 0:
                            # 1. Check Binance Price
                            exec_price = await self.exchange.get_market_price(asset)
                            if exec_price <= 0:
                                continue
                                
                            # 2. Calculate Size
                            # Binance contracts usually have min size filters, but SDK handles basic errors
                            size = allocation / exec_price
                            
                            # 3. Execute
                            if self.trading_mode == "auto":
                                result = await self.exchange.place_order(
                                    asset=asset,
                                    action=action,
                                    size=size,
                                    order_type="market"
                                )
                                self.logger.info(f"Binance Execution {asset} {action}: {result}")
                                
                                if self.on_trade_executed:
                                    self.on_trade_executed({
                                        "asset": asset,
                                        "action": action,
                                        "price": exec_price,
                                        "size": size,
                                        "venue": "Binance"
                                    })

                    self._notify_state_update()

                except Exception as e:
                    self.logger.error(f"Loop error: {e}", exc_info=True)
                    self.state.error = str(e)

                await asyncio.sleep(self._get_interval_seconds())

        except asyncio.CancelledError:
            self.logger.info("Loop cancelled")

    def _extract_indicators(self, indicators, interval):
        """Helper to safely extract indicator data"""
        data = indicators.get(interval, {})
        return {
            "ema20": (data.get("ema20") or [])[-1] if isinstance(data.get("ema20"), list) else data.get("ema20"),
            "rsi14": (data.get("rsi14") or [])[-1] if isinstance(data.get("rsi14"), list) else data.get("rsi14"),
            "macd": (data.get("macd") or [])[-1] if isinstance(data.get("macd"), list) else data.get("macd"),
        }

    def _calculate_sharpe(self, returns):
        return 0.0 # TODO: Implement

    def _get_interval_seconds(self):
        return 60 # Default 1m

    def _notify_state_update(self):
        if self.on_state_update:
            self.on_state_update(self.state)

    # ... Rest of methods (manual closing, proposals) ...
    # Can be copied from previous implementation if needed

