#!/usr/bin/env python3
"""
Demo Data Generator for Trading Bot
Generates fake trading data for demonstration purposes
"""

import os
import sys
import time
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import psycopg2
    import redis
    import requests
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Please install: pip install psycopg2-binary redis requests")
    sys.exit(1)

class DemoDataGenerator:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.redis_url = os.getenv('REDIS_URL')
        self.license_server_url = os.getenv('LICENSE_SERVER_URL', 'http://localhost:8080')
        
        # Trading pairs for demo data
        self.trading_pairs = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT',
            'XRPUSDT', 'LTCUSDT', 'LINKUSDT', 'BCHUSDT', 'XLMUSDT'
        ]
        
        # Base prices for realistic data
        self.base_prices = {
            'BTCUSDT': 45000,
            'ETHUSDT': 3000,
            'BNBUSDT': 400,
            'ADAUSDT': 0.5,
            'DOTUSDT': 8,
            'XRPUSDT': 0.6,
            'LTCUSDT': 150,
            'LINKUSDT': 15,
            'BCHUSDT': 300,
            'XLMUSDT': 0.12
        }
    
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None
    
    def connect_redis(self):
        """Connect to Redis"""
        try:
            return redis.from_url(self.redis_url)
        except Exception as e:
            print(f"Redis connection failed: {e}")
            return None
    
    def generate_price_data(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Generate realistic price data for a symbol"""
        base_price = self.base_prices.get(symbol, 100)
        data = []
        current_time = datetime.now() - timedelta(hours=hours)
        current_price = base_price
        
        for i in range(hours * 60):  # Minute-by-minute data
            # Simulate price movement with some volatility
            change_percent = random.uniform(-0.5, 0.5)  # ±0.5% per minute
            current_price *= (1 + change_percent / 100)
            
            # Add some trend
            if i % 60 == 0:  # Every hour, add trend
                trend = random.uniform(-2, 2)  # ±2% hourly trend
                current_price *= (1 + trend / 100)
            
            volume = random.uniform(1000, 10000)
            
            data.append({
                'symbol': symbol,
                'timestamp': current_time + timedelta(minutes=i),
                'open': current_price,
                'high': current_price * random.uniform(1.0, 1.02),
                'low': current_price * random.uniform(0.98, 1.0),
                'close': current_price,
                'volume': volume
            })
        
        return data
    
    def generate_trade_data(self, symbol: str, count: int = 100) -> List[Dict]:
        """Generate fake trade execution data"""
        trades = []
        base_price = self.base_prices.get(symbol, 100)
        
        for i in range(count):
            side = random.choice(['BUY', 'SELL'])
            quantity = random.uniform(0.01, 1.0)
            price = base_price * random.uniform(0.95, 1.05)
            
            trades.append({
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now() - timedelta(hours=random.randint(1, 168)),
                'status': random.choice(['FILLED', 'PARTIALLY_FILLED', 'CANCELLED']),
                'profit_loss': random.uniform(-50, 100) if side == 'SELL' else 0
            })
        
        return trades
    
    def populate_database(self):
        """Populate database with demo data"""
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    open_price DECIMAL(20,8),
                    high_price DECIMAL(20,8),
                    low_price DECIMAL(20,8),
                    close_price DECIMAL(20,8),
                    volume DECIMAL(20,8)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    quantity DECIMAL(20,8),
                    price DECIMAL(20,8),
                    timestamp TIMESTAMP NOT NULL,
                    status VARCHAR(20),
                    profit_loss DECIMAL(20,8)
                )
            """)
            
            # Generate and insert data for each trading pair
            for symbol in self.trading_pairs:
                print(f"Generating data for {symbol}...")
                
                # Price data
                price_data = self.generate_price_data(symbol)
                for data in price_data:
                    cursor.execute("""
                        INSERT INTO price_data (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data['symbol'], data['timestamp'], data['open'],
                        data['high'], data['low'], data['close'], data['volume']
                    ))
                
                # Trade data
                trade_data = self.generate_trade_data(symbol)
                for trade in trade_data:
                    cursor.execute("""
                        INSERT INTO trades (symbol, side, quantity, price, timestamp, status, profit_loss)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        trade['symbol'], trade['side'], trade['quantity'],
                        trade['price'], trade['timestamp'], trade['status'], trade['profit_loss']
                    ))
            
            conn.commit()
            print("Demo data successfully populated in database!")
            return True
            
        except Exception as e:
            print(f"Error populating database: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def populate_redis_cache(self):
        """Populate Redis with real-time demo data"""
        r = self.connect_redis()
        if not r:
            return False
        
        try:
            for symbol in self.trading_pairs:
                # Current price
                current_price = self.base_prices[symbol] * random.uniform(0.95, 1.05)
                r.set(f"price:{symbol}", json.dumps({
                    'symbol': symbol,
                    'price': current_price,
                    'change_24h': random.uniform(-10, 10),
                    'volume_24h': random.uniform(1000000, 10000000),
                    'timestamp': datetime.now().isoformat()
                }))
                
                # Order book data
                r.set(f"orderbook:{symbol}", json.dumps({
                    'bids': [[current_price * 0.999, random.uniform(1, 10)] for _ in range(10)],
                    'asks': [[current_price * 1.001, random.uniform(1, 10)] for _ in range(10)]
                }))
            
            print("Redis cache populated with demo data!")
            return True
            
        except Exception as e:
            print(f"Error populating Redis: {e}")
            return False
    
    def run_continuous_updates(self):
        """Run continuous updates to simulate live trading data"""
        print("Starting continuous demo data updates...")
        r = self.connect_redis()
        
        while True:
            try:
                for symbol in self.trading_pairs:
                    # Update current price with small random changes
                    current_data = r.get(f"price:{symbol}")
                    if current_data:
                        data = json.loads(current_data)
                        old_price = data['price']
                        # Small price movement
                        new_price = old_price * random.uniform(0.998, 1.002)
                        
                        data.update({
                            'price': new_price,
                            'change_24h': ((new_price - self.base_prices[symbol]) / self.base_prices[symbol]) * 100,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        r.set(f"price:{symbol}", json.dumps(data))
                
                time.sleep(5)  # Update every 5 seconds
                
            except KeyboardInterrupt:
                print("\nStopping demo data updates...")
                break
            except Exception as e:
                print(f"Error in continuous updates: {e}")
                time.sleep(10)

def main():
    print("Trading Bot Demo Data Generator")
    print("================================")
    
    generator = DemoDataGenerator()
    
    # Initial data population
    print("Populating database with historical data...")
    if generator.populate_database():
        print("✅ Database populated successfully")
    else:
        print("❌ Database population failed")
    
    print("Populating Redis cache...")
    if generator.populate_redis_cache():
        print("✅ Redis cache populated successfully")
    else:
        print("❌ Redis cache population failed")
    
    # Start continuous updates
    if os.getenv('DEMO_MODE') == 'true':
        generator.run_continuous_updates()
    else:
        print("Demo data generation complete!")

if __name__ == "__main__":
    main()