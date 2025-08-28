// Trading Bot Desktop Application
class TradingBotApp {
    constructor() {
        this.currentView = 'dashboard';
        this.connectionStatus = 'connected';
        this.notifications = [];
        this.settings = {};
        
        this.init();
    }
    
    async init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }
    
    async setup() {
        // Hide loading screen and show app
        setTimeout(() => {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('app-container').style.display = 'flex';
        }, 1500);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load settings from Electron
        await this.loadSettings();
        
        // Setup Electron IPC listeners
        this.setupElectronListeners();
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        console.log('Trading Bot Desktop App initialized');
    }
    
    setupEventListeners() {
        // Navigation tabs
        const navTabs = document.querySelectorAll('.nav-tab');
        navTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                this.navigateToView(view);
            });
        });
        
        // Header buttons
        const settingsBtn = document.getElementById('settings-btn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.showSettings());
        }
        
        const notificationsBtn = document.getElementById('notifications-btn');
        if (notificationsBtn) {
            notificationsBtn.addEventListener('click', () => this.showNotifications());
        }
        
        // Refresh button
        const refreshBtns = document.querySelectorAll('.btn[data-action="refresh"]');
        refreshBtns.forEach(btn => {
            btn.addEventListener('click', () => this.refreshData());
        });
        
        // Chart controls
        const chartControls = document.querySelectorAll('.chart-controls .btn');
        chartControls.forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Remove active class from siblings
                e.currentTarget.parentElement.querySelectorAll('.btn').forEach(b => {
                    b.classList.remove('active');
                });
                // Add active class to clicked button
                e.currentTarget.classList.add('active');
                
                // Update chart timeframe
                const timeframe = e.currentTarget.textContent;
                this.updateChartTimeframe(timeframe);
            });
        });
    }
    
    setupElectronListeners() {
        if (window.electronAPI) {
            // Listen for navigation events from menu
            window.electronAPI.onNavigateTo((view) => {
                this.navigateToView(view);
            });
            
            // Listen for settings dialog
            window.electronAPI.onShowSettings(() => {
                this.showSettings();
            });
        }
    }
    
    navigateToView(viewName) {
        // Hide all views
        const views = document.querySelectorAll('.view');
        views.forEach(view => {
            view.style.display = 'none';
        });
        
        // Show selected view
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.style.display = 'block';
        }
        
        // Update navigation tabs
        const navTabs = document.querySelectorAll('.nav-tab');
        navTabs.forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.view === viewName) {
                tab.classList.add('active');
            }
        });
        
        this.currentView = viewName;
        
        // Load view-specific data
        this.loadViewData(viewName);
    }
    
    async loadViewData(viewName) {
        switch (viewName) {
            case 'dashboard':
                await this.loadDashboardData();
                break;
            case 'trading':
                await this.loadTradingData();
                break;
            case 'portfolio':
                await this.loadPortfolioData();
                break;
            case 'analytics':
                await this.loadAnalyticsData();
                break;
            case 'history':
                await this.loadHistoryData();
                break;
        }
    }
    
    async loadDashboardData() {
        // Simulate loading dashboard data
        console.log('Loading dashboard data...');
        
        // Update metrics with mock data
        this.updateDashboardMetrics({
            portfolioValue: '$12,450.67',
            portfolioChange: '+2.34% (+$285.12)',
            dailyPnL: '+$285.12',
            dailyPnLChange: '+2.34%',
            winRate: '68.5%',
            winRateChange: '+1.2%',
            activeTrades: '7',
            activeTradesNote: '2 pending'
        });
    }
    
    updateDashboardMetrics(data) {
        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach((card, index) => {
            const valueEl = card.querySelector('.metric-value');
            const changeEl = card.querySelector('.metric-change');
            
            switch (index) {
                case 0: // Portfolio Value
                    if (valueEl) valueEl.textContent = data.portfolioValue;
                    if (changeEl) changeEl.textContent = data.portfolioChange;
                    break;
                case 1: // 24h P&L
                    if (valueEl) valueEl.textContent = data.dailyPnL;
                    if (changeEl) changeEl.textContent = data.dailyPnLChange;
                    break;
                case 2: // Win Rate
                    if (valueEl) valueEl.textContent = data.winRate;
                    if (changeEl) changeEl.textContent = data.winRateChange;
                    break;
                case 3: // Active Trades
                    if (valueEl) valueEl.textContent = data.activeTrades;
                    if (changeEl) changeEl.textContent = data.activeTradesNote;
                    break;
            }
        });
    }
    
    async loadTradingData() {
        console.log('Loading trading data...');
        // Implement trading data loading
    }
    
    async loadPortfolioData() {
        console.log('Loading portfolio data...');
        // Implement portfolio data loading
    }
    
    async loadAnalyticsData() {
        console.log('Loading analytics data...');
        // Implement analytics data loading
    }
    
    async loadHistoryData() {
        console.log('Loading history data...');
        // Implement history data loading
    }
    
    async loadSettings() {
        if (window.electronAPI) {
            try {
                this.settings = await window.electronAPI.getSettings();
                console.log('Settings loaded:', this.settings);
            } catch (error) {
                console.error('Failed to load settings:', error);
            }
        }
    }
    
    async saveSettings(newSettings) {
        if (window.electronAPI) {
            try {
                this.settings = await window.electronAPI.saveSettings(newSettings);
                console.log('Settings saved:', this.settings);
            } catch (error) {
                console.error('Failed to save settings:', error);
            }
        }
    }
    
    showSettings() {
        // Create settings modal/dialog
        console.log('Opening settings...');
        
        if (window.electronAPI) {
            window.electronAPI.showMessageBox({
                type: 'info',
                title: 'Settings',
                message: 'Settings panel will be implemented here',
                detail: 'This will include trading parameters, API keys, notifications, and more.'
            });
        }
    }
    
    showNotifications() {
        console.log('Opening notifications...');
        
        if (window.electronAPI) {
            window.electronAPI.showMessageBox({
                type: 'info',
                title: 'Notifications',
                message: 'You have 3 new notifications',
                detail: '• Trade executed: BTC/USDT\n• Portfolio milestone reached\n• System update available'
            });
        }
    }
    
    refreshData() {
        console.log('Refreshing data...');
        this.loadViewData(this.currentView);
        this.updateConnectionStatus();
    }
    
    updateChartTimeframe(timeframe) {
        console.log(`Updating chart timeframe to: ${timeframe}`);
        // Implement chart update logic
    }
    
    updateConnectionStatus() {
        const statusEl = document.getElementById('connection-status');
        const statusDot = statusEl?.querySelector('.status-dot');
        const statusText = statusEl?.querySelector('.status-text');
        
        if (statusDot && statusText) {
            // Simulate connection status
            const statuses = ['connected', 'connecting', 'disconnected'];
            const statusTexts = ['Connected', 'Connecting...', 'Disconnected'];
            
            // For demo, keep it connected
            const status = 'connected';
            const text = 'Connected';
            
            statusDot.className = `status-dot ${status}`;
            statusText.textContent = text;
            
            this.connectionStatus = status;
        }
    }
    
    startPeriodicUpdates() {
        // Update data every 30 seconds
        setInterval(() => {
            if (this.currentView === 'dashboard') {
                this.loadDashboardData();
            }
            this.updateConnectionStatus();
        }, 30000);
        
        // Update metrics more frequently
        setInterval(() => {
            this.simulateMetricUpdates();
        }, 5000);
    }
    
    simulateMetricUpdates() {
        // Simulate real-time metric updates
        const portfolioValues = ['$12,450.67', '$12,485.23', '$12,421.89', '$12,467.45'];
        const changes = ['+2.34% (+$285.12)', '+2.67% (+$318.45)', '+1.98% (+$241.67)', '+2.45% (+$298.23)'];
        
        const randomIndex = Math.floor(Math.random() * portfolioValues.length);
        
        this.updateDashboardMetrics({
            portfolioValue: portfolioValues[randomIndex],
            portfolioChange: changes[randomIndex],
            dailyPnL: changes[randomIndex].split(' ')[1].replace('(', '').replace(')', ''),
            dailyPnLChange: changes[randomIndex].split(' ')[0],
            winRate: '68.5%',
            winRateChange: '+1.2%',
            activeTrades: '7',
            activeTradesNote: '2 pending'
        });
    }
    
    // Utility methods
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }
    
    formatPercentage(value) {
        return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`;
    }
}

// Initialize the app
const app = new TradingBotApp();

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Application error:', event.error);
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});