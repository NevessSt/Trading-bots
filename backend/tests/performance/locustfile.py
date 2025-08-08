"""Locust load testing configuration for the trading bot platform."""
from locust import HttpUser, task, between
import json
import random
from datetime import datetime, timedelta


class TradingBotUser(HttpUser):
    """Simulates a user interacting with the trading bot platform."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts. Performs login."""
        self.register_and_login()
        self.create_api_key()
    
    def register_and_login(self):
        """Register a new user and login."""
        # Generate unique user data
        user_id = random.randint(1000, 999999)
        self.email = f"loadtest{user_id}@example.com"
        self.username = f"loadtest{user_id}"
        self.password = "LoadTest123!"
        
        # Register user
        registration_data = {
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "first_name": "Load",
            "last_name": "Test"
        }
        
        with self.client.post("/api/auth/register", 
                             json=registration_data, 
                             catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                # Simulate email verification
                verification_data = response.json()
                if 'verification_token' in verification_data:
                    self.client.post(f"/api/auth/verify-email/{verification_data['verification_token']}")
            else:
                response.failure(f"Registration failed: {response.status_code}")
        
        # Login
        login_data = {
            "email": self.email,
            "password": self.password
        }
        
        with self.client.post("/api/auth/login", 
                             json=login_data, 
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                login_response = response.json()
                self.access_token = login_response['access_token']
                self.headers = {'Authorization': f'Bearer {self.access_token}'}
            else:
                response.failure(f"Login failed: {response.status_code}")
                self.access_token = None
                self.headers = {}
    
    def create_api_key(self):
        """Create an API key for the user."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        api_key_data = {
            "name": "Load Test API Key",
            "permissions": ["read", "trade"]
        }
        
        with self.client.post("/api/api-keys", 
                             json=api_key_data, 
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                api_key_response = response.json()
                self.api_key = api_key_response['api_key']['key']
                self.api_headers = {'X-API-Key': self.api_key}
            else:
                response.failure(f"API key creation failed: {response.status_code}")
                self.api_key = None
                self.api_headers = {}
    
    @task(3)
    def view_profile(self):
        """View user profile - high frequency task."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        with self.client.get("/api/auth/profile", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Profile view failed: {response.status_code}")
    
    @task(2)
    def list_bots(self):
        """List user's trading bots."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        # Test with pagination
        page = random.randint(1, 3)
        per_page = random.choice([10, 20, 50])
        
        with self.client.get(f"/api/bots?page={page}&per_page={per_page}", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Bot listing failed: {response.status_code}")
    
    @task(1)
    def create_bot(self):
        """Create a new trading bot."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        strategies = ['grid_trading', 'dca', 'momentum', 'mean_reversion']
        exchanges = ['binance', 'coinbase', 'kraken']
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT']
        
        bot_data = {
            "name": f"Load Test Bot {random.randint(1, 1000)}",
            "strategy": random.choice(strategies),
            "exchange": random.choice(exchanges),
            "symbol": random.choice(symbols),
            "config": {
                "grid_size": random.randint(5, 20),
                "investment_amount": random.randint(100, 5000),
                "grid_spacing": round(random.uniform(0.1, 2.0), 2),
                "stop_loss": round(random.uniform(2.0, 10.0), 2),
                "take_profit": round(random.uniform(5.0, 20.0), 2)
            }
        }
        
        with self.client.post("/api/bots", 
                             json=bot_data, 
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                bot_response = response.json()
                # Store bot ID for later operations
                if not hasattr(self, 'bot_ids'):
                    self.bot_ids = []
                self.bot_ids.append(bot_response['bot']['id'])
            else:
                response.failure(f"Bot creation failed: {response.status_code}")
    
    @task(1)
    def update_bot(self):
        """Update an existing bot."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        if not hasattr(self, 'bot_ids') or not self.bot_ids:
            return
        
        bot_id = random.choice(self.bot_ids)
        update_data = {
            "name": f"Updated Load Test Bot {random.randint(1, 1000)}",
            "config": {
                "grid_size": random.randint(5, 20),
                "investment_amount": random.randint(100, 5000)
            }
        }
        
        with self.client.put(f"/api/bots/{bot_id}", 
                            json=update_data, 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Bot might have been deleted, remove from list
                self.bot_ids.remove(bot_id)
                response.success()  # Don't count as failure
            else:
                response.failure(f"Bot update failed: {response.status_code}")
    
    @task(1)
    def get_bot_performance(self):
        """Get performance metrics for a bot."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        if not hasattr(self, 'bot_ids') or not self.bot_ids:
            return
        
        bot_id = random.choice(self.bot_ids)
        
        with self.client.get(f"/api/bots/{bot_id}/performance", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Bot might have been deleted
                self.bot_ids.remove(bot_id)
                response.success()
            else:
                response.failure(f"Performance retrieval failed: {response.status_code}")
    
    @task(1)
    def get_trade_history(self):
        """Get trade history for a bot."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        if not hasattr(self, 'bot_ids') or not self.bot_ids:
            return
        
        bot_id = random.choice(self.bot_ids)
        
        # Add some query parameters
        params = {
            'limit': random.choice([10, 20, 50]),
            'offset': random.randint(0, 100)
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        with self.client.get(f"/api/bots/{bot_id}/trades?{query_string}", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                self.bot_ids.remove(bot_id)
                response.success()
            else:
                response.failure(f"Trade history retrieval failed: {response.status_code}")
    
    @task(1)
    def view_subscription(self):
        """View current subscription."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        with self.client.get("/api/subscriptions/current", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Subscription view failed: {response.status_code}")
    
    @task(1)
    def list_api_keys(self):
        """List user's API keys."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        with self.client.get("/api/api-keys", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"API keys listing failed: {response.status_code}")
    
    @task(1)
    def use_api_key_authentication(self):
        """Test API key authentication."""
        if not hasattr(self, 'api_headers') or not self.api_headers:
            return
        
        with self.client.get("/api/auth/profile", 
                            headers=self.api_headers,
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"API key auth failed: {response.status_code}")
    
    @task(1)
    def simulate_trading_activity(self):
        """Simulate trading activity."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        if not hasattr(self, 'bot_ids') or not self.bot_ids:
            return
        
        bot_id = random.choice(self.bot_ids)
        
        # Simulate a trade execution
        trade_data = {
            "symbol": random.choice(['BTCUSDT', 'ETHUSDT', 'ADAUSDT']),
            "side": random.choice(['buy', 'sell']),
            "quantity": round(random.uniform(0.001, 0.1), 6),
            "order_type": random.choice(['market', 'limit']),
            "price": round(random.uniform(30000, 70000), 2) if random.choice([True, False]) else None
        }
        
        with self.client.post(f"/api/bots/{bot_id}/trades", 
                             json=trade_data, 
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code in [201, 400]:  # 400 might be expected for invalid trades
                response.success()
            elif response.status_code == 404:
                self.bot_ids.remove(bot_id)
                response.success()
            else:
                response.failure(f"Trade simulation failed: {response.status_code}")
    
    def on_stop(self):
        """Called when a user stops. Performs cleanup."""
        if hasattr(self, 'headers') and self.headers:
            # Logout
            self.client.post("/api/auth/logout", headers=self.headers)


class AdminUser(HttpUser):
    """Simulates an admin user with elevated privileges."""
    
    wait_time = between(2, 5)
    weight = 1  # Lower weight means fewer admin users
    
    def on_start(self):
        """Login as admin user."""
        # This would require a pre-created admin account
        login_data = {
            "email": "admin@tradingbot.com",
            "password": "AdminPassword123!"
        }
        
        with self.client.post("/api/auth/login", 
                             json=login_data, 
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                login_response = response.json()
                self.access_token = login_response['access_token']
                self.headers = {'Authorization': f'Bearer {self.access_token}'}
            else:
                response.failure(f"Admin login failed: {response.status_code}")
                self.access_token = None
                self.headers = {}
    
    @task(2)
    def view_admin_dashboard(self):
        """View admin dashboard."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        with self.client.get("/api/admin/dashboard", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 if endpoint doesn't exist
                response.success()
            else:
                response.failure(f"Admin dashboard failed: {response.status_code}")
    
    @task(1)
    def list_all_users(self):
        """List all users (admin only)."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        with self.client.get("/api/admin/users", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code in [200, 404, 403]:  # Various expected responses
                response.success()
            else:
                response.failure(f"User listing failed: {response.status_code}")
    
    @task(1)
    def view_system_metrics(self):
        """View system performance metrics."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        with self.client.get("/api/admin/metrics", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code in [200, 404, 403]:
                response.success()
            else:
                response.failure(f"Metrics view failed: {response.status_code}")


class WebSocketUser(HttpUser):
    """Simulates WebSocket connections for real-time updates."""
    
    wait_time = between(5, 10)
    weight = 2  # Moderate number of WebSocket users
    
    def on_start(self):
        """Setup for WebSocket testing."""
        # Login first
        user_id = random.randint(1000, 999999)
        email = f"wstest{user_id}@example.com"
        password = "WSTest123!"
        
        # Register and login
        registration_data = {
            "email": email,
            "username": f"wstest{user_id}",
            "password": password
        }
        
        self.client.post("/api/auth/register", json=registration_data)
        
        login_data = {"email": email, "password": password}
        response = self.client.post("/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            login_response = response.json()
            self.access_token = login_response['access_token']
            self.headers = {'Authorization': f'Bearer {self.access_token}'}
        else:
            self.headers = {}
    
    @task(1)
    def get_websocket_info(self):
        """Get WebSocket connection information."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        with self.client.get("/api/websocket/info", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 if not implemented
                response.success()
            else:
                response.failure(f"WebSocket info failed: {response.status_code}")
    
    @task(1)
    def simulate_realtime_data_request(self):
        """Simulate requesting real-time market data."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        symbol = random.choice(symbols)
        
        with self.client.get(f"/api/market/realtime/{symbol}", 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 if not implemented
                response.success()
            else:
                response.failure(f"Realtime data failed: {response.status_code}")


# Custom load test scenarios
class HighLoadScenario(TradingBotUser):
    """High-load scenario with more aggressive testing."""
    
    wait_time = between(0.5, 1.5)  # Faster requests
    weight = 5  # More users of this type
    
    @task(5)
    def rapid_profile_checks(self):
        """Rapidly check profile multiple times."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        for _ in range(3):  # Make 3 rapid requests
            with self.client.get("/api/auth/profile", 
                                headers=self.headers,
                                catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Rapid profile check failed: {response.status_code}")


class StressTestScenario(TradingBotUser):
    """Stress test scenario with extreme load."""
    
    wait_time = between(0.1, 0.5)  # Very fast requests
    weight = 1  # Few users but very aggressive
    
    @task(10)
    def stress_test_endpoints(self):
        """Stress test various endpoints rapidly."""
        if not hasattr(self, 'headers') or not self.headers:
            return
        
        endpoints = [
            "/api/auth/profile",
            "/api/bots",
            "/api/subscriptions/current",
            "/api/api-keys"
        ]
        
        endpoint = random.choice(endpoints)
        
        with self.client.get(endpoint, 
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code in [200, 429]:  # 429 = rate limited, expected
                response.success()
            else:
                response.failure(f"Stress test failed: {response.status_code}")