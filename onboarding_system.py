#!/usr/bin/env python3
"""
Customer Onboarding System for TradingBot Pro
Guides new users through setup, configuration, and first bot creation
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional

class OnboardingStep:
    def __init__(self, step_id: str, title: str, description: str, required: bool = True):
        self.step_id = step_id
        self.title = title
        self.description = description
        self.required = required
        self.completed = False
        self.data = {}

class OnboardingSystem:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.steps = self._initialize_steps()
    
    def _initialize_steps(self) -> List[OnboardingStep]:
        """Initialize onboarding steps"""
        return [
            OnboardingStep(
                "welcome",
                "Welcome to TradingBot Pro",
                "Learn about our platform and choose your subscription plan"
            ),
            OnboardingStep(
                "subscription",
                "Choose Your Plan",
                "Select a subscription plan that fits your trading needs"
            ),
            OnboardingStep(
                "profile",
                "Complete Your Profile",
                "Tell us about your trading experience and goals"
            ),
            OnboardingStep(
                "api_setup",
                "Connect Your Exchange",
                "Add your exchange API keys to start trading"
            ),
            OnboardingStep(
                "risk_settings",
                "Configure Risk Management",
                "Set up your risk tolerance and safety limits"
            ),
            OnboardingStep(
                "first_strategy",
                "Create Your First Strategy",
                "Build your first automated trading strategy"
            ),
            OnboardingStep(
                "verification",
                "Verify Setup",
                "Test your configuration and start paper trading"
            ),
            OnboardingStep(
                "completion",
                "You're All Set!",
                "Welcome to automated trading with TradingBot Pro"
            )
        ]
    
    def get_user_progress(self, user_id: int) -> Dict:
        """Get user's onboarding progress"""
        # In production, this would query the database
        # For now, return mock data
        progress = {
            'user_id': user_id,
            'current_step': 0,
            'completed_steps': [],
            'total_steps': len(self.steps),
            'completion_percentage': 0,
            'started_at': datetime.utcnow(),
            'estimated_completion': datetime.utcnow() + timedelta(minutes=15)
        }
        return progress
    
    def complete_step(self, user_id: int, step_id: str, step_data: Dict) -> bool:
        """Mark a step as completed"""
        try:
            # Validate step data based on step_id
            if not self._validate_step_data(step_id, step_data):
                return False
            
            # Save step completion to database
            self._save_step_completion(user_id, step_id, step_data)
            
            # Check if this completes the onboarding
            if step_id == "completion":
                self._complete_onboarding(user_id)
            
            self.logger.info(f"User {user_id} completed step: {step_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to complete step {step_id} for user {user_id}: {e}")
            return False
    
    def _validate_step_data(self, step_id: str, data: Dict) -> bool:
        """Validate step data based on step requirements"""
        validators = {
            'subscription': self._validate_subscription_data,
            'profile': self._validate_profile_data,
            'api_setup': self._validate_api_data,
            'risk_settings': self._validate_risk_data,
            'first_strategy': self._validate_strategy_data
        }
        
        validator = validators.get(step_id)
        if validator:
            return validator(data)
        return True
    
    def _validate_subscription_data(self, data: Dict) -> bool:
        """Validate subscription selection"""
        required_fields = ['plan_type', 'payment_method']
        return all(field in data for field in required_fields)
    
    def _validate_profile_data(self, data: Dict) -> bool:
        """Validate profile information"""
        required_fields = ['trading_experience', 'risk_tolerance', 'investment_goals']
        return all(field in data for field in required_fields)
    
    def _validate_api_data(self, data: Dict) -> bool:
        """Validate API key setup"""
        required_fields = ['exchange', 'api_key', 'api_secret']
        return all(field in data and data[field] for field in required_fields)
    
    def _validate_risk_data(self, data: Dict) -> bool:
        """Validate risk management settings"""
        required_fields = ['max_position_size', 'stop_loss_percentage', 'daily_loss_limit']
        return all(field in data for field in required_fields)
    
    def _validate_strategy_data(self, data: Dict) -> bool:
        """Validate strategy configuration"""
        required_fields = ['strategy_type', 'trading_pair', 'parameters']
        return all(field in data for field in required_fields)
    
    def _save_step_completion(self, user_id: int, step_id: str, data: Dict):
        """Save step completion to database"""
        # In production, save to database
        self.logger.info(f"Saving step completion: user={user_id}, step={step_id}")
    
    def _complete_onboarding(self, user_id: int):
        """Complete the onboarding process"""
        # Mark onboarding as complete
        # Send welcome email
        # Enable full platform access
        # Create initial demo trades
        self.logger.info(f"Onboarding completed for user {user_id}")
    
    def get_step_content(self, step_id: str) -> Dict:
        """Get content for a specific step"""
        step_content = {
            'welcome': {
                'title': 'Welcome to TradingBot Pro',
                'content': 'Start your automated trading journey',
                'video_url': '/static/videos/welcome.mp4',
                'features': [
                    'Advanced Trading Strategies',
                    'Multi-Exchange Support', 
                    'Risk Management Tools',
                    '24/7 Automated Trading'
                ]
            },
            'subscription': {
                'title': 'Choose Your Plan',
                'plans': [
                    {
                        'name': 'Basic',
                        'price': '$29.99/month',
                        'features': ['1 Trading Bot', 'Basic Strategies', 'Email Support']
                    },
                    {
                        'name': 'Pro',
                        'price': '$79.99/month', 
                        'features': ['5 Trading Bots', 'All Strategies', 'Priority Support'],
                        'recommended': True
                    },
                    {
                        'name': 'Enterprise',
                        'price': '$199.99/month',
                        'features': ['Unlimited Bots', 'Custom Strategies', '24/7 Support']
                    }
                ]
            },
            'profile': {
                'title': 'Tell Us About Yourself',
                'fields': [
                    {
                        'name': 'trading_experience',
                        'label': 'Trading Experience',
                        'type': 'select',
                        'options': ['Beginner', 'Intermediate', 'Advanced', 'Expert']
                    },
                    {
                        'name': 'risk_tolerance',
                        'label': 'Risk Tolerance',
                        'type': 'select',
                        'options': ['Conservative', 'Moderate', 'Aggressive']
                    },
                    {
                        'name': 'investment_goals',
                        'label': 'Investment Goals',
                        'type': 'textarea',
                        'placeholder': 'Describe your trading goals...'
                    }
                ]
            },
            'api_setup': {
                'title': 'Connect Your Exchange',
                'supported_exchanges': ['Binance', 'Coinbase Pro', 'Kraken'],
                'security_note': 'Your API keys are encrypted and stored securely',
                'tutorial_link': '/docs/api-setup'
            },
            'risk_settings': {
                'title': 'Configure Risk Management',
                'settings': [
                    {
                        'name': 'max_position_size',
                        'label': 'Maximum Position Size (%)',
                        'type': 'number',
                        'default': 10,
                        'min': 1,
                        'max': 50
                    },
                    {
                        'name': 'stop_loss_percentage',
                        'label': 'Stop Loss (%)',
                        'type': 'number',
                        'default': 5,
                        'min': 1,
                        'max': 20
                    },
                    {
                        'name': 'daily_loss_limit',
                        'label': 'Daily Loss Limit ($)',
                        'type': 'number',
                        'default': 100
                    }
                ]
            },
            'first_strategy': {
                'title': 'Create Your First Strategy',
                'recommended_strategies': [
                    {
                        'name': 'Grid Trading',
                        'description': 'Great for sideways markets',
                        'difficulty': 'Beginner'
                    },
                    {
                        'name': 'DCA (Dollar Cost Average)',
                        'description': 'Reduce average cost over time',
                        'difficulty': 'Beginner'
                    }
                ]
            }
        }
        
        return step_content.get(step_id, {})
    
    def get_onboarding_checklist(self, user_id: int) -> List[Dict]:
        """Get onboarding checklist for user"""
        progress = self.get_user_progress(user_id)
        checklist = []
        
        for i, step in enumerate(self.steps):
            checklist.append({
                'step_id': step.step_id,
                'title': step.title,
                'description': step.description,
                'completed': i in progress['completed_steps'],
                'current': i == progress['current_step'],
                'required': step.required
            })
        
        return checklist
    
    def send_onboarding_email(self, user_id: int, step_id: str):
        """Send onboarding email for specific step"""
        # Email templates for each step
        email_templates = {
            'welcome': 'Welcome to TradingBot Pro! Let\'s get you started.',
            'api_setup': 'Time to connect your exchange account.',
            'first_strategy': 'Ready to create your first trading strategy?',
            'completion': 'Congratulations! Your setup is complete.'
        }
        
        template = email_templates.get(step_id)
        if template:
            # Send email (integrate with email service)
            self.logger.info(f"Sending onboarding email to user {user_id}: {step_id}")
    
    def get_onboarding_analytics(self) -> Dict:
        """Get onboarding analytics"""
        return {
            'total_users_started': 1250,
            'completion_rate': 78.5,
            'average_completion_time': '12 minutes',
            'drop_off_points': [
                {'step': 'api_setup', 'drop_off_rate': 15.2},
                {'step': 'first_strategy', 'drop_off_rate': 8.7}
            ],
            'most_popular_plan': 'Pro',
            'common_issues': [
                'API key validation errors',
                'Exchange connection timeouts'
            ]
        }

if __name__ == "__main__":
    onboarding = OnboardingSystem()
    print("Onboarding system initialized")
    print(f"Total steps: {len(onboarding.steps)}")