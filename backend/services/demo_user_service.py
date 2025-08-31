"""Demo user management and auto-expiration service."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_, or_

from models import User, License, db
from services.logging_service import get_logger, LogCategory
from services.license_service import LicenseService
from services.email_service import EmailService

logger = get_logger(LogCategory.SYSTEM)


class DemoUserService:
    """Service for managing demo users and their auto-expiration."""
    
    def __init__(self):
        self.license_service = LicenseService()
        self.email_service = EmailService()
    
    def create_demo_user(self, email: str, password_hash: str, 
                        demo_duration_days: int = 7) -> User:
        """Create a new demo user with automatic expiration.
        
        Args:
            email: User's email address
            password_hash: Hashed password
            demo_duration_days: Number of days before demo expires
            
        Returns:
            Created User object
        """
        try:
            # Calculate expiration date
            expires_at = datetime.utcnow() + timedelta(days=demo_duration_days)
            
            # Create user with demo license
            user = User(
                email=email,
                password_hash=password_hash,
                is_demo=True,
                demo_expires_at=expires_at,
                is_active=True,
                email_verified=True,  # Auto-verify demo accounts
                created_at=datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create demo license
            demo_license = self.license_service.create_demo_license(
                user_id=user.id,
                duration_days=demo_duration_days
            )
            
            db.session.commit()
            
            logger.info(f"Created demo user {email} with {demo_duration_days} day expiration")
            
            # Send welcome email
            self._send_demo_welcome_email(user, demo_duration_days)
            
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create demo user {email}: {e}")
            raise
    
    def get_expiring_demo_users(self, days_before_expiry: int = 1) -> List[User]:
        """Get demo users that will expire within specified days.
        
        Args:
            days_before_expiry: Number of days before expiry to check
            
        Returns:
            List of User objects expiring soon
        """
        try:
            expiry_threshold = datetime.utcnow() + timedelta(days=days_before_expiry)
            
            users = User.query.filter(
                and_(
                    User.is_demo == True,
                    User.is_active == True,
                    User.demo_expires_at <= expiry_threshold,
                    User.demo_expires_at > datetime.utcnow()
                )
            ).all()
            
            return users
            
        except Exception as e:
            logger.error(f"Failed to get expiring demo users: {e}")
            return []
    
    def get_expired_demo_users(self) -> List[User]:
        """Get demo users that have already expired.
        
        Returns:
            List of expired User objects
        """
        try:
            users = User.query.filter(
                and_(
                    User.is_demo == True,
                    User.is_active == True,
                    User.demo_expires_at <= datetime.utcnow()
                )
            ).all()
            
            return users
            
        except Exception as e:
            logger.error(f"Failed to get expired demo users: {e}")
            return []
    
    def expire_demo_user(self, user: User, send_notification: bool = True) -> bool:
        """Expire a demo user account.
        
        Args:
            user: User object to expire
            send_notification: Whether to send expiration notification
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Deactivate user
            user.is_active = False
            user.expired_at = datetime.utcnow()
            
            # Deactivate all user's licenses
            licenses = License.query.filter_by(user_id=user.id, is_active=True).all()
            for license in licenses:
                license.is_active = False
                license.deactivated_at = datetime.utcnow()
            
            # Clear sensitive data but keep user record for analytics
            user.api_keys = []  # Clear API keys
            
            db.session.commit()
            
            logger.info(f"Expired demo user {user.email}")
            
            # Send expiration notification
            if send_notification:
                self._send_demo_expiration_email(user)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to expire demo user {user.email}: {e}")
            return False
    
    def extend_demo_user(self, user: User, additional_days: int) -> bool:
        """Extend a demo user's expiration date.
        
        Args:
            user: User object to extend
            additional_days: Number of additional days to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not user.is_demo:
                raise ValueError("User is not a demo user")
            
            # Extend expiration date
            if user.demo_expires_at:
                user.demo_expires_at += timedelta(days=additional_days)
            else:
                user.demo_expires_at = datetime.utcnow() + timedelta(days=additional_days)
            
            # Extend licenses
            licenses = License.query.filter_by(user_id=user.id).all()
            for license in licenses:
                if license.expires_at:
                    license.expires_at += timedelta(days=additional_days)
            
            db.session.commit()
            
            logger.info(f"Extended demo user {user.email} by {additional_days} days")
            
            # Send extension notification
            self._send_demo_extension_email(user, additional_days)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to extend demo user {user.email}: {e}")
            return False
    
    def cleanup_expired_demo_users(self, batch_size: int = 100) -> Dict[str, int]:
        """Clean up expired demo users in batches.
        
        Args:
            batch_size: Number of users to process in each batch
            
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            'processed': 0,
            'expired': 0,
            'errors': 0,
            'notifications_sent': 0
        }
        
        try:
            # Get expired users in batches
            offset = 0
            while True:
                expired_users = User.query.filter(
                    and_(
                        User.is_demo == True,
                        User.is_active == True,
                        User.demo_expires_at <= datetime.utcnow()
                    )
                ).offset(offset).limit(batch_size).all()
                
                if not expired_users:
                    break
                
                for user in expired_users:
                    stats['processed'] += 1
                    
                    try:
                        if self.expire_demo_user(user, send_notification=True):
                            stats['expired'] += 1
                            stats['notifications_sent'] += 1
                        else:
                            stats['errors'] += 1
                    except Exception as e:
                        logger.error(f"Error expiring demo user {user.email}: {e}")
                        stats['errors'] += 1
                
                offset += batch_size
            
            logger.info(f"Demo user cleanup completed: {stats}")
            
        except Exception as e:
            logger.error(f"Demo user cleanup failed: {e}")
            stats['errors'] += 1
        
        return stats
    
    def send_expiration_warnings(self, days_before: int = 1) -> Dict[str, int]:
        """Send expiration warnings to demo users.
        
        Args:
            days_before: Number of days before expiry to send warning
            
        Returns:
            Dictionary with warning statistics
        """
        stats = {
            'processed': 0,
            'warnings_sent': 0,
            'errors': 0
        }
        
        try:
            expiring_users = self.get_expiring_demo_users(days_before)
            
            for user in expiring_users:
                stats['processed'] += 1
                
                try:
                    self._send_demo_warning_email(user, days_before)
                    stats['warnings_sent'] += 1
                except Exception as e:
                    logger.error(f"Failed to send warning to {user.email}: {e}")
                    stats['errors'] += 1
            
            logger.info(f"Demo expiration warnings sent: {stats}")
            
        except Exception as e:
            logger.error(f"Failed to send expiration warnings: {e}")
            stats['errors'] += 1
        
        return stats
    
    def get_demo_user_stats(self) -> Dict[str, int]:
        """Get statistics about demo users.
        
        Returns:
            Dictionary with demo user statistics
        """
        try:
            stats = {
                'total_demo_users': User.query.filter_by(is_demo=True).count(),
                'active_demo_users': User.query.filter(
                    and_(User.is_demo == True, User.is_active == True)
                ).count(),
                'expired_demo_users': User.query.filter(
                    and_(
                        User.is_demo == True,
                        User.is_active == False,
                        User.expired_at.isnot(None)
                    )
                ).count(),
                'expiring_soon': len(self.get_expiring_demo_users(3)),  # Next 3 days
                'overdue_expiration': len(self.get_expired_demo_users())
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get demo user stats: {e}")
            return {}
    
    def _send_demo_welcome_email(self, user: User, demo_days: int):
        """Send welcome email to new demo user."""
        try:
            subject = "Welcome to Your Demo Account!"
            
            body = f"""
            Welcome to our trading platform!
            
            Your demo account has been created and is valid for {demo_days} days.
            
            Demo Account Details:
            - Email: {user.email}
            - Expires: {user.demo_expires_at.strftime('%Y-%m-%d %H:%M UTC')}
            - Features: Full access to all demo features
            
            Get started:
            1. Log in to your account
            2. Explore the dashboard
            3. Try our trading strategies
            4. Monitor your portfolio
            
            Need help? Contact our support team.
            
            Upgrade to a full account anytime to keep your data and continue trading!
            """
            
            self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                body=body
            )
            
        except Exception as e:
            logger.error(f"Failed to send demo welcome email to {user.email}: {e}")
    
    def _send_demo_warning_email(self, user: User, days_remaining: int):
        """Send expiration warning email to demo user."""
        try:
            subject = f"Demo Account Expires in {days_remaining} Day{'s' if days_remaining != 1 else ''}!"
            
            body = f"""
            Your demo account is expiring soon!
            
            Account Details:
            - Email: {user.email}
            - Expires: {user.demo_expires_at.strftime('%Y-%m-%d %H:%M UTC')}
            - Time Remaining: {days_remaining} day{'s' if days_remaining != 1 else ''}
            
            Don't lose your progress! Upgrade to a full account to:
            - Keep all your trading data
            - Continue using our platform
            - Access premium features
            - Get priority support
            
            Upgrade now to avoid losing access to your account.
            """
            
            self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                body=body
            )
            
        except Exception as e:
            logger.error(f"Failed to send demo warning email to {user.email}: {e}")
    
    def _send_demo_expiration_email(self, user: User):
        """Send expiration notification email to demo user."""
        try:
            subject = "Demo Account Has Expired"
            
            body = f"""
            Your demo account has expired.
            
            Account Details:
            - Email: {user.email}
            - Expired: {user.expired_at.strftime('%Y-%m-%d %H:%M UTC')}
            
            Thank you for trying our platform! We hope you enjoyed the experience.
            
            To continue using our services:
            1. Sign up for a full account
            2. Choose a subscription plan
            3. Keep all your trading strategies
            
            We'd love to have you back as a full member!
            """
            
            self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                body=body
            )
            
        except Exception as e:
            logger.error(f"Failed to send demo expiration email to {user.email}: {e}")
    
    def _send_demo_extension_email(self, user: User, additional_days: int):
        """Send extension notification email to demo user."""
        try:
            subject = "Demo Account Extended!"
            
            body = f"""
            Great news! Your demo account has been extended.
            
            Extension Details:
            - Email: {user.email}
            - Additional Days: {additional_days}
            - New Expiration: {user.demo_expires_at.strftime('%Y-%m-%d %H:%M UTC')}
            
            Continue exploring our platform and make the most of your extended demo period!
            
            Consider upgrading to a full account for unlimited access.
            """
            
            self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                body=body
            )
            
        except Exception as e:
            logger.error(f"Failed to send demo extension email to {user.email}: {e}")