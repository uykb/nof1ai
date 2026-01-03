"""
Binance Exchange Adapter (Official SDK)
Wraps the binance-connector to provide a unified interface for the TradingBotEngine.
Focuses on USDT-M Futures.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from binance.um_futures import UMFutures
from src.backend.config_loader import CONFIG
from binance.error import ClientError

logger = logging.getLogger(__name__)

class BinanceAPI:
    """
    Wrapper for Binance Official Python Connector (UM Futures).
    Handles authentication, order management, and account state retrieval.
    """

    def __init__(self):
        self.api_key = CONFIG.get("binance_api_key")
        self.secret_key = CONFIG.get("binance_secret_key")
        self.use_testnet = CONFIG.get("binance_testnet", False)
        
        self.client = None
        
        if self.api_key and self.secret_key:
            try:
                base_url = 'https://testnet.binancefuture.com' if self.use_testnet else 'https://fapi.binance.com'
                self.client = UMFutures(
                    key=self.api_key, 
                    secret=self.secret_key,
                    base_url=base_url
                )
                logger.info(f"BinanceAPI initialized (Testnet: {self.use_testnet})")
            except Exception as e:
                logger.error(f"Failed to initialize BinanceAPI: {e}")
        else:
            logger.warning("Binance keys missing. Trading functionality disabled.")

    async def get_user_state(self) -> Dict[str, Any]:
        """
        Fetch account balance and open positions (USDT-M Futures).
        Returns normalized structure compatible with BotEngine.
        """
        if not self.client:
            return {"margin_summary": {}, "asset_positions": []}

        try:
            # 1. Get Account Info (Balances & Positions)
            # This endpoint returns both balances and positions
            account_info = await asyncio.to_thread(self.client.account)
            
            # 2. Extract Margin/Balance Info
            # In USDT-M futures, we look for USDT balance
            total_wallet_balance = float(account_info.get('totalWalletBalance', 0.0))
            total_unrealized_pnl = float(account_info.get('totalUnrealizedProfit', 0.0))
            total_margin_balance = float(account_info.get('totalMarginBalance', 0.0))
            available_balance = float(account_info.get('availableBalance', 0.0))
            
            normalized_state = {
                "margin_summary": {
                    "account_value": total_margin_balance,  # Equity = Wallet + Unrealized PnL
                    "total_n_usd": total_wallet_balance,    # Wallet Balance
                    "withdrawable": available_balance,
                    "unrealized_pnl": total_unrealized_pnl
                },
                "asset_positions": []
            }

            # 3. Extract Active Positions
            # Filter for non-zero positions
            for pos in account_info.get("positions", []):
                amt = float(pos.get("positionAmt", 0.0))
                if amt != 0:
                    symbol = pos.get("symbol")
                    # Remove USDT suffix for cleaner display if needed, but Binance uses full symbols like BTCUSDT
                    
                    normalized_state["asset_positions"].append({
                        "coin": symbol, # Keep full symbol for Binance
                        "position": {
                            "szi": amt,
                            "entryPx": float(pos.get("entryPrice", 0)),
                            "unrealizedPnl": float(pos.get("unrealizedProfit", 0)),
                            "leverage": {
                                "type": "cross" if pos.get("isolated") == False else "isolated",
                                "value": float(pos.get("leverage", 1))
                            },
                            "liquidationPx": 0.0, # Not always in account info, might need risky endpoint
                            "marginUsed": float(pos.get("initialMargin", 0))
                        }
                    })

            return normalized_state

        except ClientError as e:
            logger.error(f"Binance API Error (get_user_state): {e.error_message}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error fetching Binance user state: {e}")
            return {"error": str(e)}

    async def place_order(self, asset: str, action: str, size: float, price: float = None, order_type: str = "market") -> Dict[str, Any]:
        """
        Place order on Binance Futures.
        
        Args:
            asset: Symbol (e.g., "BTC", "ETH" -> automatically appends USDT if needed)
            action: "buy" or "sell"
            size: Quantity
            price: Limit price
            order_type: "limit" or "market"
        """
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}

        try:
            # Normalize symbol: Ensure it ends with USDT
            symbol = asset.upper()
            if not symbol.endswith("USDT"):
                symbol += "USDT"
            
            side = action.upper() # BUY/SELL
            type_str = order_type.upper()
            
            params = {
                "symbol": symbol,
                "side": side,
                "type": type_str,
                "quantity": size,
            }
            
            if type_str == "LIMIT":
                if price is None:
                    return {"status": "error", "message": "Limit price required"}
                params["price"] = price
                params["timeInForce"] = "GTC" # Good Till Cancel
            
            logger.info(f"Placing Binance Order: {params}")
            
            response = await asyncio.to_thread(self.client.new_order, **params)
            
            return {
                "status": "filled" if response.get("status") == "FILLED" else "open",
                "order_id": response.get("orderId"),
                "avg_price": float(response.get("avgPrice", 0.0)),
                "response": response
            }

        except ClientError as e:
            logger.error(f"Binance Order Failed: {e.error_message}")
            return {"status": "error", "message": e.error_message}
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {"status": "error", "message": str(e)}

    async def cancel_order(self, asset: str, order_id: int) -> bool:
        """Cancel specific order."""
        if not self.client:
            return False
        
        try:
            symbol = asset.upper()
            if not symbol.endswith("USDT"):
                symbol += "USDT"
                
            await asyncio.to_thread(self.client.cancel_order, symbol=symbol, orderId=order_id)
            return True
        except Exception as e:
            logger.error(f"Cancel failed: {e}")
            return False

    async def get_market_price(self, asset: str) -> float:
        """Get current Mark Price."""
        if not self.client:
            return 0.0
            
        try:
            symbol = asset.upper()
            if not symbol.endswith("USDT"):
                symbol += "USDT"
            
            # Using Mark Price for futures
            response = await asyncio.to_thread(self.client.mark_price, symbol=symbol)
            return float(response.get("markPrice", 0.0))
        except Exception as e:
            logger.error(f"Price fetch failed: {e}")
            return 0.0

    async def get_open_orders(self, asset: str = None) -> List[Dict[str, Any]]:
        """Get all open orders."""
        if not self.client:
            return []
            
        try:
            symbol = None
            if asset:
                symbol = asset.upper()
                if not symbol.endswith("USDT"):
                    symbol += "USDT"
            
            orders = await asyncio.to_thread(self.client.get_orders, symbol=symbol) if symbol else await asyncio.to_thread(self.client.get_orders)
            
            # Filter specifically for 'NEW' or 'PARTIALLY_FILLED' status just in case
            active_orders = [o for o in orders if o.get("status") in ["NEW", "PARTIALLY_FILLED"]]
            
            return active_orders
        except Exception as e:
            logger.error(f"Fetch open orders failed: {e}")
            return []
