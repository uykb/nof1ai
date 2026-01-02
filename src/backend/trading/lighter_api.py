"""
Lighter.xyz Exchange Adapter
Wraps the lighter-sdk to provide a unified interface for the TradingBotEngine.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from lighter.lighter_client import Client
from lighter.modules.blockchain.utils import get_account_from_private_key
from src.backend.config_loader import CONFIG

logger = logging.getLogger(__name__)

class LighterAPI:
    """
    Asynchronous wrapper for Lighter.xyz SDK.
    Handles authentication, order management, and account state retrieval.
    """

    def __init__(self):
        self.api_key = CONFIG.get("lighter_api_key")
        self.private_key = CONFIG.get("lighter_private_key")
        self.web3_private_key = CONFIG.get("lighter_web3_private_key")
        self.client = None
        self.account = None
        
        # Initialize client if keys are present
        if self.api_key and self.private_key and self.web3_private_key:
            try:
                # Assuming standard initialization for lighter-sdk
                # Note: Exact init might vary based on SDK version, adjusting to standard pattern
                self.client = Client(
                    api_key=self.api_key,
                    api_secret=self.private_key, 
                    web3_private_key=self.web3_private_key
                )
                logger.info("LighterAPI initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LighterAPI: {e}")
        else:
            logger.warning("LighterAPI keys missing. Trading functionality will be disabled.")

    async def get_user_state(self, address: str = None) -> Dict[str, Any]:
        """
        Fetch account portfolio, balances, and open positions.
        Returns a normalized dictionary compatible with BotEngine.
        """
        if not self.client:
            return {"margin_summary": {}, "cross_margin_summary": {}, "asset_positions": []}

        try:
            # Wrap synchronous SDK call in thread
            # Assuming client.get_portfolio() returns the full state
            portfolio = await asyncio.to_thread(self.client.get_portfolio)
            
            # Normalize data structure to match what BotEngine expects (Hyperliquid-like structure)
            # This allows us to minimize changes in the engine logic
            normalized_state = {
                "margin_summary": {
                    "account_value": float(portfolio.get("total_value", 0)),
                    "total_margin_used": float(portfolio.get("margin_used", 0)),
                    "total_n_usd": float(portfolio.get("balance", 0)), # Available balance
                    "withdrawable": float(portfolio.get("withdrawable", 0)),
                },
                "asset_positions": []
            }

            # Transform positions
            for pos in portfolio.get("positions", []):
                normalized_state["asset_positions"].append({
                    "coin": pos.get("symbol", "").replace("-PERP", ""), # Normalize symbol
                    "position": {
                        "szi": float(pos.get("size", 0)),
                        "entryPx": float(pos.get("entry_price", 0)),
                        "unrealizedPnl": float(pos.get("unrealized_pnl", 0)),
                        "leverage": {
                            "type": "cross", 
                            "value": float(pos.get("leverage", 1))
                        },
                        "liquidationPx": float(pos.get("liquidation_price", 0)),
                        "marginUsed": float(pos.get("margin_used", 0))
                    }
                })

            return normalized_state

        except Exception as e:
            logger.error(f"Error fetching user state: {e}")
            return {"error": str(e)}

    async def place_order(self, asset: str, action: str, size: float, price: float = None, order_type: str = "limit") -> Dict[str, Any]:
        """
        Place an order on Lighter.
        
        Args:
            asset: Symbol (e.g., "BTC", "ETH")
            action: "buy" or "sell"
            size: Quantity
            price: Limit price (None for market)
            order_type: "limit" or "market"
        """
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}

        try:
            symbol = f"{asset}-PERP" # Lighter usually uses suffix
            side = action.upper() # BUY/SELL
            
            logger.info(f"Placing order: {side} {size} {symbol} @ {price or 'MARKET'}")

            # SDK call
            if order_type.lower() == "market":
                # Assuming create_market_order signature
                result = await asyncio.to_thread(
                    self.client.create_market_order,
                    symbol=symbol,
                    side=side,
                    size=size
                )
            else:
                # Limit order
                result = await asyncio.to_thread(
                    self.client.create_limit_order,
                    symbol=symbol,
                    side=side,
                    size=size,
                    price=price
                )
            
            return {
                "status": "filled" if order_type == "market" else "open",
                "order_id": result.get("order_id"),
                "response": result
            }

        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {"status": "error", "message": str(e)}

    async def cancel_order(self, asset: str, order_id: str) -> bool:
        """Cancel a specific order."""
        if not self.client:
            return False
            
        try:
            await asyncio.to_thread(
                self.client.cancel_order,
                order_id=order_id,
                symbol=f"{asset}-PERP"
            )
            return True
        except Exception as e:
            logger.error(f"Cancel failed: {e}")
            return False

    async def get_market_price(self, asset: str) -> float:
        """Get current market price for an asset."""
        if not self.client:
            return 0.0
            
        try:
            # Assuming get_order_book or get_ticker
            ticker = await asyncio.to_thread(
                self.client.get_ticker,
                symbol=f"{asset}-PERP"
            )
            return float(ticker.get("last_price", 0))
        except Exception as e:
            logger.error(f"Price fetch failed: {e}")
            return 0.0

    async def get_open_orders(self, asset: str = None) -> List[Dict[str, Any]]:
        """Get all open orders."""
        if not self.client:
            return []
            
        try:
            orders = await asyncio.to_thread(self.client.get_open_orders)
            
            # Filter by asset if needed
            if asset:
                orders = [o for o in orders if asset in o.get("symbol", "")]
                
            return orders
        except Exception as e:
            logger.error(f"Fetch open orders failed: {e}")
            return []
