from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

support_bp = Blueprint('support', __name__)

@support_bp.route('/contact', methods=['POST'])
def submit_contact_form():
    """
    Handle contact form submissions from users
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field.title()} is required'
                }), 400
        
        # Get user info if authenticated
        user_email = None
        try:
            verify_jwt_in_request(optional=True)
            user_identity = get_jwt_identity()
            if user_identity:
                user_email = user_identity
        except:
            pass  # User not authenticated, that's okay
        
        # Prepare contact data
        contact_data = {
            'name': data['name'].strip(),
            'email': data['email'].strip().lower(),
            'subject': data['subject'].strip(),
            'message': data['message'].strip(),
            'priority': data.get('priority', 'medium'),
            'user_email': user_email,
            'timestamp': datetime.now().isoformat(),
            'ip_address': request.remote_addr
        }
        
        # Send email notification to support team
        if _send_support_notification(contact_data):
            # Send confirmation email to user
            _send_user_confirmation(contact_data)
            
            return jsonify({
                'success': True,
                'message': 'Your message has been sent successfully. We will get back to you soon.'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send message. Please try again later.'
            }), 500
            
    except Exception as e:
        logger.error(f"Contact form submission error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your request'
        }), 500

def _send_support_notification(contact_data):
    """
    Send email notification to support team
    """
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        support_email = os.getenv('SUPPORT_EMAIL', smtp_username)
        
        if not smtp_username or not smtp_password:
            logger.warning("SMTP credentials not configured")
            return False
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = support_email
        msg['Subject'] = f"[{contact_data['priority'].upper()}] Support Request: {contact_data['subject']}"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>New Support Request</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Name:</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{contact_data['name']}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Email:</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{contact_data['email']}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Subject:</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{contact_data['subject']}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Priority:</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{contact_data['priority'].title()}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">User Account:</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{contact_data['user_email'] or 'Not logged in'}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">Timestamp:</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{contact_data['timestamp']}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold;">IP Address:</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{contact_data['ip_address']}</td>
                </tr>
            </table>
            
            <h3>Message:</h3>
            <div style="border: 1px solid #ddd; padding: 15px; background-color: #f9f9f9; white-space: pre-wrap;">{contact_data['message']}</div>
            
            <hr>
            <p><em>This is an automated message from the Trading Bot Platform support system.</em></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Support notification sent for contact from {contact_data['email']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send support notification: {str(e)}")
        return False

def _send_user_confirmation(contact_data):
    """
    Send confirmation email to user
    """
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not smtp_username or not smtp_password:
            return False
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = contact_data['email']
        msg['Subject'] = "We've received your message - Trading Bot Platform"
        
        # Estimate response time based on priority
        response_times = {
            'high': '2-4 hours',
            'medium': '12-24 hours',
            'low': '24-48 hours'
        }
        expected_response = response_times.get(contact_data['priority'], '24-48 hours')
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Thank you for contacting us!</h2>
            <p>Dear {contact_data['name']},</p>
            
            <p>We have received your message and will get back to you as soon as possible.</p>
            
            <div style="border: 1px solid #ddd; padding: 15px; background-color: #f0f8ff; margin: 20px 0;">
                <h3>Your Message Details:</h3>
                <p><strong>Subject:</strong> {contact_data['subject']}</p>
                <p><strong>Priority:</strong> {contact_data['priority'].title()}</p>
                <p><strong>Expected Response Time:</strong> {expected_response}</p>
                <p><strong>Submitted:</strong> {contact_data['timestamp']}</p>
            </div>
            
            <p>If you have any urgent issues, please don't hesitate to reach out to us directly at support@tradingbot.com or call +1 (555) 123-4567.</p>
            
            <p>Best regards,<br>
            Trading Bot Platform Support Team</p>
            
            <hr>
            <p style="font-size: 12px; color: #666;"><em>This is an automated confirmation email. Please do not reply to this message.</em></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Confirmation email sent to {contact_data['email']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send user confirmation: {str(e)}")
        return False

@support_bp.route('/faq', methods=['GET'])
def get_faq():
    """
    Get frequently asked questions
    """
    faq_data = [
        {
            'category': 'General',
            'questions': [
                {
                    'question': 'Is my money safe on the platform?',
                    'answer': 'The platform never holds your funds. All trading happens directly on your exchange account using API keys. We only facilitate trade execution.'
                },
                {
                    'question': 'How much should I start with?',
                    'answer': 'We recommend starting with at least $100-500 for meaningful results. Start small and scale up as you gain confidence.'
                },
                {
                    'question': 'Do I need trading experience?',
                    'answer': 'No, but basic understanding of trading concepts is helpful. Start with paper trading and our beginner-friendly strategies.'
                }
            ]
        },
        {
            'category': 'Technical',
            'questions': [
                {
                    'question': 'What exchanges do you support?',
                    'answer': 'Currently Binance, Coinbase Pro, and Kraken. More exchanges are added regularly.'
                },
                {
                    'question': 'Can I run multiple strategies simultaneously?',
                    'answer': 'Yes, Pro and Enterprise plans support multiple bots with different strategies.'
                },
                {
                    'question': 'How often do bots check for trading opportunities?',
                    'answer': 'Bots check every minute for new signals based on your chosen timeframe.'
                }
            ]
        },
        {
            'category': 'Billing',
            'questions': [
                {
                    'question': 'Can I cancel my subscription anytime?',
                    'answer': 'Yes, you can cancel anytime. You\'ll retain access until the end of your billing period.'
                },
                {
                    'question': 'Do you offer refunds?',
                    'answer': 'We offer a 7-day money-back guarantee for first-time subscribers.'
                },
                {
                    'question': 'What payment methods do you accept?',
                    'answer': 'We accept all major credit cards, PayPal, and cryptocurrency payments.'
                }
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'data': faq_data
    })