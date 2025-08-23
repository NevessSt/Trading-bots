#!/usr/bin/env python3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email_config():
    """Test SMTP email configuration"""
    print("Testing email configuration...")
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    print(f"SMTP Server: {smtp_server}:{smtp_port}")
    print(f"Username: {smtp_username}")
    print(f"Password: {'*' * len(smtp_password) if smtp_password else 'Not set'}")
    
    if not smtp_username or not smtp_password:
        print("❌ SMTP credentials not configured!")
        print("Please update your .env file with:")
        print("SMTP_USERNAME=your-actual-email@gmail.com")
        print("SMTP_PASSWORD=your-16-character-app-password")
        return False
    
    if smtp_username == 'your-actual-email@gmail.com' or smtp_password == 'your-16-character-app-password':
        print("❌ SMTP credentials are still placeholder values!")
        print("Please replace with your actual Gmail credentials.")
        return False
    
    try:
        print("Attempting SMTP connection...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.quit()
        print("✅ SMTP connection successful!")
        return True
    except Exception as e:
        print(f"❌ SMTP connection failed: {str(e)}")
        print("\nCommon issues:")
        print("1. Make sure you're using an App Password, not your regular Gmail password")
        print("2. Enable 2-Factor Authentication on your Gmail account")
        print("3. Generate App Password at: https://myaccount.google.com/apppasswords")
        print("4. Make sure 'Less secure app access' is enabled (if not using App Password)")
        return False

def send_test_email(to_email):
    """Send a test verification email"""
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = "Test Email - Trading Bot Platform"
        
        body = """
        <html>
        <body>
            <h2>Email Configuration Test</h2>
            <p>This is a test email to verify your SMTP configuration is working.</p>
            <p>If you received this email, your email verification system is properly configured!</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Test email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {str(e)}")
        return False

if __name__ == '__main__':
    print("=== Email Configuration Test ===")
    
    if test_email_config():
        test_email = input("\nEnter an email address to send a test email (or press Enter to skip): ").strip()
        if test_email:
            send_test_email(test_email)
    
    print("\n=== Test Complete ===")