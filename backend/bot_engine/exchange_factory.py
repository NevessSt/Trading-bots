from typing import Dict, Any, Optional
from .exchange_manager import ExchangeManager

class ExchangeFactory:
    """Factory class for creating exchange instances"""
    
    def __init__(self):
        self._exchanges = {}
        self.exchange_manager = ExchangeManager()
    
    def create_exchange(self, exchange_name: str, config: Dict[str, Any]) -> Optional[Any]:
        """Create an exchange instance"""
        try:
            # Use the exchange manager to get exchange instance
            return self.exchange_manager.get_exchange(exchange_name)
        except Exception as e:
            print(f"Error creating exchange {exchange_name}: {e}")
            return None
    
    def get_supported_exchanges(self) -> list:
        """Get list of supported exchanges"""
        return ['binance', 'coinbase', 'kraken']
    
    def is_exchange_supported(self, exchange_name: str) -> bool:
        """Check if exchange is supported"""
        return exchange_name.lower() in self.get_supported_exchanges()