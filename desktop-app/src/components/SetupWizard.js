const { ipcRenderer } = require('electron');

class SetupWizard {
  constructor() {
    this.currentStep = 0;
    this.formData = {
      exchange: '',
      apiKey: '',
      apiSecret: '',
      defaultStrategy: 'dca',
      maxPortfolioRisk: 5,
      stopLossPercentage: 2,
      takeProfitPercentage: 5,
      maxPositionSize: 10,
      dailyLossLimit: 1000,
      notifications: true
    };
    
    this.steps = [
      { id: 'welcome', title: 'Welcome', template: 'welcome' },
      { id: 'exchange', title: 'Exchange Setup', template: 'exchange' },
      { id: 'preferences', title: 'Trading Preferences', template: 'preferences' },
      { id: 'risk', title: 'Risk Management', template: 'risk' },
      { id: 'complete', title: 'Complete', template: 'complete' }
    ];
    
    this.init();
  }

  init() {
    // Check if setup was already completed
    const setupCompleted = localStorage.getItem('setupCompleted');
    const setupSkipped = localStorage.getItem('setupSkipped');
    
    if (!setupCompleted && !setupSkipped) {
      this.showWizard();
    }
  }

  showWizard() {
    // Create wizard window
    const wizardHtml = this.generateWizardHTML();
    document.body.innerHTML = wizardHtml;
    this.bindEvents();
    this.renderCurrentStep();
  }

  generateWizardHTML() {
    return `
      <div id="setup-wizard" class="wizard-container">
        <div class="wizard-header">
          <h1>Trading Bot Setup</h1>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${(this.currentStep / (this.steps.length - 1)) * 100}%"></div>
          </div>
          <div class="step-indicators">
            ${this.steps.map((step, index) => `
              <div class="step-indicator ${index <= this.currentStep ? 'active' : ''}">
                <span class="step-number">${index + 1}</span>
                <span class="step-title">${step.title}</span>
              </div>
            `).join('')}
          </div>
        </div>
        
        <div class="wizard-content" id="wizard-content">
          <!-- Dynamic content will be inserted here -->
        </div>
        
        <div class="wizard-footer">
          <button id="prev-btn" class="btn btn-secondary" style="display: none;">Previous</button>
          <div class="footer-right">
            <button id="skip-btn" class="btn btn-link">Skip Setup</button>
            <button id="next-btn" class="btn btn-primary">Continue</button>
          </div>
        </div>
      </div>
      
      <style>
        .wizard-container {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .wizard-header {
          text-align: center;
          margin-bottom: 40px;
        }
        
        .wizard-header h1 {
          color: #1f2937;
          margin-bottom: 20px;
        }
        
        .progress-bar {
          width: 100%;
          height: 4px;
          background: #e5e7eb;
          border-radius: 2px;
          margin-bottom: 20px;
          overflow: hidden;
        }
        
        .progress-fill {
          height: 100%;
          background: #3b82f6;
          transition: width 0.3s ease;
        }
        
        .step-indicators {
          display: flex;
          justify-content: space-between;
          margin-top: 20px;
        }
        
        .step-indicator {
          text-align: center;
          flex: 1;
        }
        
        .step-indicator.active .step-number {
          background: #3b82f6;
          color: white;
        }
        
        .step-number {
          display: inline-block;
          width: 30px;
          height: 30px;
          line-height: 30px;
          border-radius: 50%;
          background: #e5e7eb;
          color: #6b7280;
          font-weight: bold;
          margin-bottom: 5px;
        }
        
        .step-title {
          display: block;
          font-size: 12px;
          color: #6b7280;
        }
        
        .wizard-content {
          background: white;
          border-radius: 8px;
          padding: 40px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          margin-bottom: 30px;
          min-height: 400px;
        }
        
        .wizard-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .footer-right {
          display: flex;
          gap: 10px;
        }
        
        .btn {
          padding: 10px 20px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }
        
        .btn-primary {
          background: #3b82f6;
          color: white;
        }
        
        .btn-primary:hover {
          background: #2563eb;
        }
        
        .btn-secondary {
          background: #e5e7eb;
          color: #374151;
        }
        
        .btn-secondary:hover {
          background: #d1d5db;
        }
        
        .btn-link {
          background: none;
          color: #6b7280;
          text-decoration: underline;
        }
        
        .btn-link:hover {
          color: #374151;
        }
        
        .form-group {
          margin-bottom: 20px;
        }
        
        .form-label {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
          color: #374151;
        }
        
        .form-input {
          width: 100%;
          padding: 10px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 14px;
        }
        
        .form-input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .form-select {
          width: 100%;
          padding: 10px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          background: white;
        }
        
        .exchange-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-top: 15px;
        }
        
        .exchange-option {
          padding: 20px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          cursor: pointer;
          text-align: center;
          transition: all 0.2s;
        }
        
        .exchange-option:hover {
          border-color: #3b82f6;
        }
        
        .exchange-option.selected {
          border-color: #3b82f6;
          background: #eff6ff;
        }
        
        .risk-slider {
          width: 100%;
          margin: 10px 0;
        }
        
        .alert {
          padding: 15px;
          border-radius: 6px;
          margin-bottom: 20px;
        }
        
        .alert-warning {
          background: #fef3c7;
          border: 1px solid #f59e0b;
          color: #92400e;
        }
        
        .alert-success {
          background: #d1fae5;
          border: 1px solid #10b981;
          color: #065f46;
        }
        
        .text-center {
          text-align: center;
        }
        
        .mb-4 {
          margin-bottom: 1rem;
        }
        
        .text-lg {
          font-size: 1.125rem;
        }
        
        .font-bold {
          font-weight: 700;
        }
      </style>
    `;
  }

  bindEvents() {
    const nextBtn = document.getElementById('next-btn');
    const prevBtn = document.getElementById('prev-btn');
    const skipBtn = document.getElementById('skip-btn');

    nextBtn.addEventListener('click', () => this.nextStep());
    prevBtn.addEventListener('click', () => this.prevStep());
    skipBtn.addEventListener('click', () => this.skipSetup());
  }

  renderCurrentStep() {
    const content = document.getElementById('wizard-content');
    const step = this.steps[this.currentStep];
    
    content.innerHTML = this.getStepContent(step.template);
    this.updateNavigation();
    this.bindStepEvents();
  }

  getStepContent(template) {
    switch (template) {
      case 'welcome':
        return `
          <div class="text-center">
            <h2 class="text-lg font-bold mb-4">Welcome to Trading Bot Pro</h2>
            <p class="mb-4">This wizard will help you set up your trading bot safely and securely.</p>
            
            <div class="alert alert-warning">
              <strong>Important:</strong> Never invest more than you can afford to lose. 
              Cryptocurrency trading involves substantial risk.
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px;">
              <div style="text-align: center; padding: 20px; background: #f0fdf4; border-radius: 8px;">
                <h4>🔒 Secure</h4>
                <p>API-only access, no withdrawals</p>
              </div>
              <div style="text-align: center; padding: 20px; background: #eff6ff; border-radius: 8px;">
                <h4>📈 Profitable</h4>
                <p>Proven strategies with backtesting</p>
              </div>
              <div style="text-align: center; padding: 20px; background: #faf5ff; border-radius: 8px;">
                <h4>⚙️ Customizable</h4>
                <p>Tailored to your risk tolerance</p>
              </div>
            </div>
          </div>
        `;
        
      case 'exchange':
        return `
          <h2 class="text-lg font-bold mb-4">Connect Your Exchange</h2>
          <p class="mb-4">Choose your exchange and enter your API credentials.</p>
          
          <div class="form-group">
            <label class="form-label">Select Exchange</label>
            <div class="exchange-grid">
              <div class="exchange-option ${this.formData.exchange === 'binance' ? 'selected' : ''}" data-exchange="binance">
                <strong>Binance</strong>
                <p>Most popular exchange</p>
              </div>
              <div class="exchange-option ${this.formData.exchange === 'coinbase' ? 'selected' : ''}" data-exchange="coinbase">
                <strong>Coinbase Pro</strong>
                <p>US-based exchange</p>
              </div>
              <div class="exchange-option ${this.formData.exchange === 'kraken' ? 'selected' : ''}" data-exchange="kraken">
                <strong>Kraken</strong>
                <p>European exchange</p>
              </div>
            </div>
          </div>
          
          ${this.formData.exchange ? `
            <div class="form-group">
              <label class="form-label">API Key</label>
              <input type="text" class="form-input" id="api-key" value="${this.formData.apiKey}" placeholder="Enter your API key">
            </div>
            
            <div class="form-group">
              <label class="form-label">API Secret</label>
              <input type="password" class="form-input" id="api-secret" value="${this.formData.apiSecret}" placeholder="Enter your API secret">
            </div>
            
            <div class="alert alert-warning">
              <strong>Security Tip:</strong> Make sure to create API keys with only "Spot Trading" permissions. 
              Never enable withdrawal permissions.
            </div>
          ` : ''}
        `;
        
      case 'preferences':
        return `
          <h2 class="text-lg font-bold mb-4">Trading Preferences</h2>
          <p class="mb-4">Configure your default trading strategy and preferences.</p>
          
          <div class="form-group">
            <label class="form-label">Default Trading Strategy</label>
            <select class="form-select" id="strategy">
              <option value="dca" ${this.formData.defaultStrategy === 'dca' ? 'selected' : ''}>Dollar Cost Averaging (Low Risk)</option>
              <option value="grid" ${this.formData.defaultStrategy === 'grid' ? 'selected' : ''}>Grid Trading (Medium Risk)</option>
              <option value="scalping" ${this.formData.defaultStrategy === 'scalping' ? 'selected' : ''}>Scalping (High Risk)</option>
              <option value="manual" ${this.formData.defaultStrategy === 'manual' ? 'selected' : ''}>Manual Trading</option>
            </select>
          </div>
          
          <div class="form-group">
            <label class="form-label">Trading Pairs</label>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 10px;">
              <label><input type="checkbox" checked> BTC/USDT</label>
              <label><input type="checkbox"> ETH/USDT</label>
              <label><input type="checkbox"> BNB/USDT</label>
              <label><input type="checkbox"> ADA/USDT</label>
            </div>
          </div>
        `;
        
      case 'risk':
        return `
          <h2 class="text-lg font-bold mb-4">Risk Management</h2>
          <p class="mb-4">Set up safety limits to protect your capital.</p>
          
          <div class="alert alert-warning">
            <strong>Critical:</strong> These settings help prevent large losses. Start conservative!
          </div>
          
          <div class="form-group">
            <label class="form-label">Maximum Portfolio Risk: <span id="portfolio-risk-value">${this.formData.maxPortfolioRisk}%</span></label>
            <input type="range" class="risk-slider" id="portfolio-risk" min="1" max="20" value="${this.formData.maxPortfolioRisk}">
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #6b7280;">
              <span>Conservative (1%)</span>
              <span>Aggressive (20%)</span>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Default Stop Loss: <span id="stop-loss-value">${this.formData.stopLossPercentage}%</span></label>
            <input type="range" class="risk-slider" id="stop-loss" min="0.5" max="10" step="0.5" value="${this.formData.stopLossPercentage}">
          </div>
          
          <div class="form-group">
            <label class="form-label">Default Take Profit: <span id="take-profit-value">${this.formData.takeProfitPercentage}%</span></label>
            <input type="range" class="risk-slider" id="take-profit" min="1" max="20" step="0.5" value="${this.formData.takeProfitPercentage}">
          </div>
          
          <div class="form-group">
            <label class="form-label">Daily Loss Limit ($)</label>
            <input type="number" class="form-input" id="daily-limit" value="${this.formData.dailyLossLimit}" placeholder="Enter daily loss limit">
          </div>
        `;
        
      case 'complete':
        return `
          <div class="text-center">
            <div class="alert alert-success">
              <h2 class="text-lg font-bold mb-4">🎉 Setup Complete!</h2>
              <p>Your trading bot is now configured and ready to use.</p>
            </div>
            
            <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: left;">
              <h3>Configuration Summary:</h3>
              <ul style="margin-top: 10px;">
                <li><strong>Exchange:</strong> ${this.formData.exchange?.toUpperCase()}</li>
                <li><strong>Strategy:</strong> ${this.formData.defaultStrategy?.toUpperCase()}</li>
                <li><strong>Portfolio Risk:</strong> ${this.formData.maxPortfolioRisk}%</li>
                <li><strong>Stop Loss:</strong> ${this.formData.stopLossPercentage}%</li>
                <li><strong>Daily Limit:</strong> $${this.formData.dailyLossLimit}</li>
              </ul>
            </div>
            
            <div class="alert alert-warning">
              <strong>Next Steps:</strong><br>
              1. Start with paper trading to test your strategy<br>
              2. Begin with small amounts for live trading<br>
              3. Monitor your trades regularly<br>
              4. Adjust settings based on performance
            </div>
          </div>
        `;
        
      default:
        return '<p>Step not found</p>';
    }
  }

  bindStepEvents() {
    // Exchange selection
    const exchangeOptions = document.querySelectorAll('.exchange-option');
    exchangeOptions.forEach(option => {
      option.addEventListener('click', (e) => {
        exchangeOptions.forEach(opt => opt.classList.remove('selected'));
        option.classList.add('selected');
        this.formData.exchange = option.dataset.exchange;
        this.renderCurrentStep(); // Re-render to show API fields
      });
    });

    // Form inputs
    const apiKey = document.getElementById('api-key');
    const apiSecret = document.getElementById('api-secret');
    const strategy = document.getElementById('strategy');
    const portfolioRisk = document.getElementById('portfolio-risk');
    const stopLoss = document.getElementById('stop-loss');
    const takeProfit = document.getElementById('take-profit');
    const dailyLimit = document.getElementById('daily-limit');

    if (apiKey) apiKey.addEventListener('input', (e) => this.formData.apiKey = e.target.value);
    if (apiSecret) apiSecret.addEventListener('input', (e) => this.formData.apiSecret = e.target.value);
    if (strategy) strategy.addEventListener('change', (e) => this.formData.defaultStrategy = e.target.value);
    if (dailyLimit) dailyLimit.addEventListener('input', (e) => this.formData.dailyLossLimit = parseInt(e.target.value));

    // Risk sliders with live updates
    if (portfolioRisk) {
      portfolioRisk.addEventListener('input', (e) => {
        this.formData.maxPortfolioRisk = parseInt(e.target.value);
        document.getElementById('portfolio-risk-value').textContent = e.target.value + '%';
      });
    }

    if (stopLoss) {
      stopLoss.addEventListener('input', (e) => {
        this.formData.stopLossPercentage = parseFloat(e.target.value);
        document.getElementById('stop-loss-value').textContent = e.target.value + '%';
      });
    }

    if (takeProfit) {
      takeProfit.addEventListener('input', (e) => {
        this.formData.takeProfitPercentage = parseFloat(e.target.value);
        document.getElementById('take-profit-value').textContent = e.target.value + '%';
      });
    }
  }

  updateNavigation() {
    const nextBtn = document.getElementById('next-btn');
    const prevBtn = document.getElementById('prev-btn');
    const skipBtn = document.getElementById('skip-btn');

    // Show/hide previous button
    prevBtn.style.display = this.currentStep > 0 ? 'block' : 'none';

    // Update next button text
    if (this.currentStep === this.steps.length - 1) {
      nextBtn.textContent = 'Start Trading';
      skipBtn.style.display = 'none';
    } else {
      nextBtn.textContent = 'Continue';
      skipBtn.style.display = 'block';
    }

    // Update progress
    const progressFill = document.querySelector('.progress-fill');
    progressFill.style.width = `${(this.currentStep / (this.steps.length - 1)) * 100}%`;

    // Update step indicators
    const indicators = document.querySelectorAll('.step-indicator');
    indicators.forEach((indicator, index) => {
      if (index <= this.currentStep) {
        indicator.classList.add('active');
      } else {
        indicator.classList.remove('active');
      }
    });
  }

  nextStep() {
    if (this.currentStep === this.steps.length - 1) {
      this.completeSetup();
      return;
    }

    if (this.validateCurrentStep()) {
      this.currentStep++;
      this.renderCurrentStep();
    }
  }

  prevStep() {
    if (this.currentStep > 0) {
      this.currentStep--;
      this.renderCurrentStep();
    }
  }

  validateCurrentStep() {
    switch (this.currentStep) {
      case 1: // Exchange step
        if (!this.formData.exchange) {
          alert('Please select an exchange');
          return false;
        }
        if (!this.formData.apiKey || !this.formData.apiSecret) {
          alert('Please enter your API credentials');
          return false;
        }
        break;
      case 2: // Preferences step
        if (!this.formData.defaultStrategy) {
          alert('Please select a trading strategy');
          return false;
        }
        break;
    }
    return true;
  }

  completeSetup() {
    // Save configuration
    localStorage.setItem('tradingBotConfig', JSON.stringify(this.formData));
    localStorage.setItem('setupCompleted', 'true');
    
    // Send configuration to main process
    ipcRenderer.send('setup-completed', this.formData);
    
    // Reload the main application
    window.location.reload();
  }

  skipSetup() {
    if (confirm('Are you sure you want to skip the setup? You can run it again later from the settings.')) {
      localStorage.setItem('setupSkipped', 'true');
      window.location.reload();
    }
  }
}

// Auto-initialize when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new SetupWizard());
} else {
  new SetupWizard();
}

module.exports = SetupWizard;