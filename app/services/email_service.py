from datetime import datetime, timedelta
from typing import Optional

from jinja2 import Template
from loguru import logger
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, Email, Mail, To

from app.core.config import settings


class EmailService:
    """Service for sending emails via Twilio SendGrid"""

    def __init__(self):
        if not settings.SENDGRID_API_KEY:
            logger.critical("SENDGRID_API_KEY is not set. Email service is disabled.")
            self.client = None
        else:
            self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    def send_email(
        self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None
    ) -> bool:
        """Send email via SendGrid"""
        if not self.client:
            logger.error("Email sending is disabled because SENDGRID_API_KEY is not configured.")
            return False

        try:
            from_email = Email(settings.EMAIL_FROM)
            to_email_obj = To(to_email)

            # Create message
            message = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                html_content=Content("text/html", html_content),
            )

            # Add plain text version if provided
            if text_content:
                message.add_content(Content("text/plain", text_content))

            # Send email
            response = self.client.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(
                    f"Email sent successfully to {to_email} (Status: {response.status_code})"
                )
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_team_invitation_email(
        self,
        to_email: str,
        inviter_name: str,
        role_name: str,
        invitation_token: str,
        message: Optional[str] = None,
    ) -> bool:
        """Send team member invitation email"""

        accept_url = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation_token}"

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                    background-color: #f4f4f4;
                }
                .email-container {
                    background: white;
                    margin: 20px;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }
                .header h1 {
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }
                .header p {
                    margin: 10px 0 0 0;
                    font-size: 16px;
                    opacity: 0.9;
                }
                .content {
                    padding: 40px 30px;
                }
                .content p {
                    margin: 15px 0;
                    font-size: 15px;
                }
                .button-container {
                    text-align: center;
                    margin: 30px 0;
                }
                .button {
                    display: inline-block;
                    padding: 15px 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white !important;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                }
                .info-box {
                    background: #f8f9fa;
                    padding: 20px;
                    border-left: 4px solid #667eea;
                    margin: 25px 0;
                    border-radius: 5px;
                }
                .info-box strong {
                    color: #667eea;
                    display: block;
                    margin-bottom: 5px;
                }
                .warning {
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    display: flex;
                    align-items: center;
                }
                .warning-icon {
                    font-size: 24px;
                    margin-right: 10px;
                }
                .link-box {
                    background: #f8f9fa;
                    padding: 15px;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    word-break: break-all;
                    font-size: 13px;
                    color: #666;
                    margin: 15px 0;
                }
                .features {
                    margin: 25px 0;
                }
                .features ul {
                    list-style: none;
                    padding: 0;
                }
                .features li {
                    padding: 8px 0;
                    padding-left: 25px;
                    position: relative;
                }
                .features li:before {
                    content: "✓";
                    position: absolute;
                    left: 0;
                    color: #667eea;
                    font-weight: bold;
                }
                .footer {
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    font-size: 13px;
                    color: #666;
                    border-top: 1px solid #e0e0e0;
                }
                .footer p {
                    margin: 5px 0;
                }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🎉 You're Invited!</h1>
                    <p>Join {{ app_name }} Team</p>
                </div>
                
                <div class="content">
                    <p>Hello,</p>
                    
                    <p><strong>{{ inviter_name }}</strong> has invited you to join the <strong>{{ app_name }}</strong> team as a <strong>{{ role_name }}</strong>.</p>
                    
                    {% if message %}
                    <div class="info-box">
                        <strong>Personal Message:</strong>
                        <p style="margin: 10px 0 0 0;">{{ message }}</p>
                    </div>
                    {% endif %}
                    
                    <div class="info-box">
                        <strong>Your Role: {{ role_name }}</strong>
                        <p style="margin: 10px 0 0 0;">This role will give you access to specific features and permissions within the system.</p>
                    </div>
                    
                    <div class="button-container">
                        <a href="{{ accept_url }}" class="button">Accept Invitation</a>
                    </div>
                    
                    <p style="font-size: 13px; color: #666;">Or copy and paste this link into your browser:</p>
                    <div class="link-box">
                        {{ accept_url }}
                    </div>
                    
                    <div class="warning">
                        <span class="warning-icon">⏰</span>
                        <div>
                            <strong>Note:</strong> This invitation will expire in 7 days.
                        </div>
                    </div>
                    
                    <div class="features">
                        <p><strong>When you click the button above, you'll be able to:</strong></p>
                        <ul>
                            <li>Create your account</li>
                            <li>Set your password</li>
                            <li>Access the system with your assigned role</li>
                        </ul>
                    </div>
                    
                    <p style="font-size: 13px; color: #666; margin-top: 30px;">If you didn't expect this invitation, you can safely ignore this email.</p>
                </div>
                
                <div class="footer">
                    <p><strong>{{ app_name }}</strong></p>
                    <p>Background Checks & Clearance Investigations</p>
                    <p style="margin-top: 15px;">This is an automated email, please do not reply.</p>
                    <p>If you need assistance, contact us at {{ support_email }}</p>
                </div>
            </div>
        </body>
        </html>
        """

        template = Template(html_template)
        html_content = template.render(
            app_name=settings.APP_NAME,
            inviter_name=inviter_name,
            role_name=role_name,
            accept_url=accept_url,
            message=message,
            support_email=settings.SUPPORT_EMAIL or "support@bcci-system.com",
        )

        text_content = f"""
You're Invited to Join {settings.APP_NAME}!

{inviter_name} has invited you to join the {settings.APP_NAME} team as a {role_name}.

{f'Personal Message: {message}' if message else ''}

To accept this invitation and create your account, visit:
{accept_url}

This invitation will expire in 7 days.

If you didn't expect this invitation, you can safely ignore this email.

---
{settings.APP_NAME} - Background Checks & Clearance Investigations
        """

        subject = f"Invitation to Join {settings.APP_NAME} as {role_name}"

        return self.send_email(to_email, subject, html_content, text_content)

    def send_client_invitation_email(
        self,
        to_email: str,
        inviter_name: str,
        company_name: str,
        invitation_token: str,
        message: Optional[str] = None,
    ) -> bool:
        """Send client company invitation email"""

        accept_url = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation_token}"

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                    background-color: #f4f4f4;
                }
                .email-container {
                    background: white;
                    margin: 20px;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header {
                    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }
                .header h1 {
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }
                .header p {
                    margin: 10px 0 0 0;
                    font-size: 16px;
                    opacity: 0.9;
                }
                .content {
                    padding: 40px 30px;
                }
                .content p {
                    margin: 15px 0;
                    font-size: 15px;
                }
                .button-container {
                    text-align: center;
                    margin: 30px 0;
                }
                .button {
                    display: inline-block;
                    padding: 15px 40px;
                    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                    color: white !important;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4);
                }
                .info-box {
                    background: #f8f9fa;
                    padding: 20px;
                    border-left: 4px solid #11998e;
                    margin: 25px 0;
                    border-radius: 5px;
                }
                .info-box strong {
                    color: #11998e;
                    display: block;
                    margin-bottom: 5px;
                }
                .feature {
                    display: flex;
                    align-items: flex-start;
                    margin: 15px 0;
                    padding: 12px;
                    background: #f8f9fa;
                    border-radius: 5px;
                }
                .feature-icon {
                    font-size: 24px;
                    margin-right: 15px;
                    flex-shrink: 0;
                }
                .warning {
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    display: flex;
                    align-items: center;
                }
                .warning-icon {
                    font-size: 24px;
                    margin-right: 10px;
                }
                .link-box {
                    background: #f8f9fa;
                    padding: 15px;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    word-break: break-all;
                    font-size: 13px;
                    color: #666;
                    margin: 15px 0;
                }
                .features-list ul {
                    list-style: none;
                    padding: 0;
                }
                .features-list li {
                    padding: 8px 0;
                    padding-left: 25px;
                    position: relative;
                }
                .features-list li:before {
                    content: "✓";
                    position: absolute;
                    left: 0;
                    color: #11998e;
                    font-weight: bold;
                }
                .footer {
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    font-size: 13px;
                    color: #666;
                    border-top: 1px solid #e0e0e0;
                }
                .footer p {
                    margin: 5px 0;
                }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🤝 Welcome to {{ app_name }}</h1>
                    <p>Your Company Has Been Onboarded</p>
                </div>
                
                <div class="content">
                    <p>Hello,</p>
                    
                    <p><strong>{{ inviter_name }}</strong> from {{ app_name }} has invited <strong>{{ company_name }}</strong> to join our platform.</p>
                    
                    {% if message %}
                    <div class="info-box">
                        <strong>Message from {{ app_name }}:</strong>
                        <p style="margin: 10px 0 0 0;">{{ message }}</p>
                    </div>
                    {% endif %}
                    
                    <div class="info-box">
                        <strong>Company: {{ company_name }}</strong>
                        <p style="margin: 10px 0 0 0;">You will have access to request and manage background checks for your employees.</p>
                    </div>
                    
                    <h3 style="color: #11998e; margin-top: 30px;">What You Can Do:</h3>
                    <div class="feature">
                        <span class="feature-icon">✅</span>
                        <span>Submit background check requests for employees</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">📊</span>
                        <span>Track application status in real-time</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">📄</span>
                        <span>Access and download completed reports</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">👥</span>
                        <span>Manage your company's users</span>
                    </div>
                    
                    <div class="button-container">
                        <a href="{{ accept_url }}" class="button">Complete Registration</a>
                    </div>
                    
                    <p style="font-size: 13px; color: #666;">Or copy and paste this link into your browser:</p>
                    <div class="link-box">
                        {{ accept_url }}
                    </div>
                    
                    <div class="warning">
                        <span class="warning-icon">⏰</span>
                        <div>
                            <strong>Note:</strong> This invitation will expire in 7 days.
                        </div>
                    </div>
                    
                    <div class="features-list">
                        <p><strong>When you click the button above, you'll be able to:</strong></p>
                        <ul>
                            <li>Create your account</li>
                            <li>Set up your profile</li>
                            <li>Start submitting background check requests</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>{{ app_name }}</strong></p>
                    <p>Background Checks & Clearance Investigations</p>
                    <p style="margin-top: 15px;">This is an automated email, please do not reply.</p>
                    <p>Need help? Contact us at {{ support_email }}</p>
                </div>
            </div>
        </body>
        </html>
        """

        template = Template(html_template)
        html_content = template.render(
            app_name=settings.APP_NAME,
            inviter_name=inviter_name,
            company_name=company_name,
            accept_url=accept_url,
            message=message,
            support_email=settings.SUPPORT_EMAIL or "support@bcci-system.com",
        )

        text_content = f"""
Welcome to {settings.APP_NAME}!

{inviter_name} has invited {company_name} to join our platform.

{f'Message: {message}' if message else ''}

What you can do:
- Submit background check requests for employees
- Track application status in real-time
- Access and download completed reports
- Manage your company's users

To complete your registration and create your account, visit:
{accept_url}

This invitation will expire in 7 days.

---
{settings.APP_NAME} - Background Checks & Clearance Investigations
        """

        subject = f"Welcome to {settings.APP_NAME} - Complete Your Registration"

        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_reset_code_email(
        self, to_email: str, user_name: str, reset_code: str, ip_address: str, user_agent: str
    ) -> bool:
        """Send password reset code email"""

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                    background-color: #f4f4f4;
                }
                .email-container {
                    background: white;
                    margin: 20px;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }
                .header h1 {
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }
                .content {
                    padding: 40px 30px;
                }
                .code-box {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    padding: 20px;
                    text-align: center;
                    border-radius: 10px;
                    margin: 30px 0;
                    box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
                }
                .info-box {
                    background: #f8f9fa;
                    padding: 20px;
                    border-left: 4px solid #f5576c;
                    margin: 25px 0;
                    border-radius: 5px;
                }
                .warning {
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .security-info {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    font-size: 13px;
                    color: #666;
                    margin: 20px 0;
                }
                .footer {
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    font-size: 13px;
                    color: #666;
                    border-top: 1px solid #e0e0e0;
                }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                
                <div class="content">
                    <p>Hello <strong>{{ user_name }}</strong>,</p>
                    
                    <p>We received a request to reset your password for your {{ app_name }} account.</p>
                    
                    <p>Your password reset code is:</p>
                    
                    <div class="code-box">
                        {{ reset_code }}
                    </div>
                    
                    <div class="warning">
                        <p><strong>⏰ This code will expire in 15 minutes.</strong></p>
                    </div>
                    
                    <div class="info-box">
                        <p><strong>How to reset your password:</strong></p>
                        <ol style="margin: 10px 0;">
                            <li>Enter this code on the password reset page</li>
                            <li>Create a new strong password</li>
                            <li>Confirm your new password</li>
                        </ol>
                    </div>
                    
                    <div class="security-info">
                        <p><strong>Request Details:</strong></p>
                        <p>📍 IP Address: {{ ip_address }}</p>
                        <p>💻 Device: {{ user_agent }}</p>
                        <p>🕐 Time: {{ timestamp }}</p>
                    </div>
                    
                    <p style="color: #d9534f; font-weight: 600;">⚠️ If you didn't request this password reset, please ignore this email and secure your account immediately.</p>
                    
                    <p style="font-size: 13px; color: #666; margin-top: 30px;">For security reasons, this code can only be used once and will expire in 15 minutes.</p>
                </div>
                
                <div class="footer">
                    <p><strong>{{ app_name }}</strong></p>
                    <p>Background Checks & Clearance Investigations</p>
                    <p style="margin-top: 15px;">This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

        from jinja2 import Template

        from app.core.config import settings

        template = Template(html_template)
        html_content = template.render(
            app_name=settings.APP_NAME,
            user_name=user_name,
            reset_code=reset_code,
            ip_address=ip_address,
            user_agent=self._parse_user_agent(user_agent),
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

        text_content = f"""
Password Reset Request

Hello {user_name},

We received a request to reset your password for your {settings.APP_NAME} account.

Your password reset code is: {reset_code}

This code will expire in 15 minutes.

Request Details:
- IP Address: {ip_address}
- Device: {user_agent}
- Time: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

If you didn't request this password reset, please ignore this email and secure your account immediately.

---
{settings.APP_NAME}
        """

        subject = f"Password Reset Code for {settings.APP_NAME}"

        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_changed_notification_email(
        self,
        to_email: str,
        user_name: str,
        ip_address: str,
        user_agent: str,
        change_type: str = "change",  # "change" or "reset"
    ) -> bool:
        """Send password changed notification email"""

        action_text = "changed" if change_type == "change" else "reset"

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                    background-color: #f4f4f4;
                }
                .email-container {
                    background: white;
                    margin: 20px;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }
                .header h1 {
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }
                .content {
                    padding: 40px 30px;
                }
                .success-box {
                    background: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 25px 0;
                    text-align: center;
                }
                .success-icon {
                    font-size: 48px;
                    margin-bottom: 10px;
                }
                .info-card {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                .info-row {
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #e0e0e0;
                }
                .info-row:last-child {
                    border-bottom: none;
                }
                .info-label {
                    font-weight: 600;
                    color: #666;
                }
                .info-value {
                    color: #333;
                    text-align: right;
                }
                .warning-box {
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 25px 0;
                }
                .button-container {
                    text-align: center;
                    margin: 30px 0;
                }
                .button {
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white !important;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: 600;
                }
                .footer {
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    font-size: 13px;
                    color: #666;
                    border-top: 1px solid #e0e0e0;
                }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>✅ Password {{ action_text|title }}</h1>
                </div>
                
                <div class="content">
                    <p>Hello <strong>{{ user_name }}</strong>,</p>
                    
                    <div class="success-box">
                        <div class="success-icon">✓</div>
                        <h3 style="margin: 10px 0;">Password Successfully {{ action_text|title }}</h3>
                        <p style="margin: 10px 0;">Your password has been {{ action_text }}d successfully.</p>
                    </div>
                    
                    <p>This is a confirmation that your {{ app_name }} account password was {{ action_text }}d.</p>
                    
                    <div class="info-card">
                        <h4 style="margin-top: 0; color: #667eea;">Change Details</h4>
                        <div class="info-row">
                            <span class="info-label">📅 Date & Time:</span>
                            <span class="info-value">{{ timestamp }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">📍 IP Address:</span>
                            <span class="info-value">{{ ip_address }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">💻 Device:</span>
                            <span class="info-value">{{ device_name }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">🌐 Browser:</span>
                            <span class="info-value">{{ browser_name }}</span>
                        </div>
                        {% if location %}
                        <div class="info-row">
                            <span class="info-label">🗺️ Location:</span>
                            <span class="info-value">{{ location }}</span>
                        </div>
                        {% endif %}
                    </div>
                    
                    <div class="warning-box">
                        <p style="margin: 0;"><strong>⚠️ Didn't {{ action_text }} your password?</strong></p>
                        <p style="margin: 10px 0 0 0;">If you didn't {{ action_text }} your password, your account may be compromised. Please contact our support team immediately.</p>
                        <div class="button-container">
                            <a href="{{ support_url }}" class="button">Contact Support</a>
                        </div>
                    </div>
                    
                    <h4>Security Tips:</h4>
                    <ul style="line-height: 1.8;">
                        <li>Never share your password with anyone</li>
                        <li>Use a unique password for this account</li>
                        <li>Enable two-factor authentication for extra security</li>
                        <li>Review your account activity regularly</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p><strong>{{ app_name }}</strong></p>
                    <p>Background Checks & Clearance Investigations</p>
                    <p style="margin-top: 15px;">This is an automated security notification.</p>
                    <p>If you have concerns, contact us at {{ support_email }}</p>
                </div>
            </div>
        </body>
        </html>
        """

        # from jinja2 import Template
        from app.core.config import settings

        device_info = self._parse_user_agent(user_agent)

        template = Template(html_template)
        html_content = template.render(
            app_name=settings.APP_NAME,
            user_name=user_name,
            action_text=action_text,
            timestamp=datetime.utcnow().strftime("%B %d, %Y at %H:%M:%S UTC"),
            ip_address=ip_address,
            device_name=device_info.get("device", "Unknown Device"),
            browser_name=device_info.get("browser", "Unknown Browser"),
            location=self._get_location_from_ip(ip_address),
            support_url=f"{settings.FRONTEND_URL}/support",
            support_email=settings.SUPPORT_EMAIL or "support@bcci-system.com",
        )

        text_content = f"""
Password Successfully {action_text.title()}

Hello {user_name},

Your password has been {action_text}d successfully.

Change Details:
- Date & Time: {datetime.utcnow().strftime("%B %d, %Y at %H:%M:%S UTC")}
- IP Address: {ip_address}
- Device: {user_agent}

If you didn't {action_text} your password, your account may be compromised. 
Please contact our support team immediately.

Security Tips:
- Never share your password with anyone
- Use a unique password for this account
- Enable two-factor authentication for extra security
- Review your account activity regularly

---
{settings.APP_NAME}
        """

        subject = f"Password {action_text.title()}d - {settings.APP_NAME}"

        return self.send_email(to_email, subject, html_content, text_content)

    def _parse_user_agent(self, user_agent: str) -> dict:
        """Parse user agent string to extract device and browser info"""
        ua_lower = user_agent.lower()

        # Detect browser
        if "chrome" in ua_lower and "edg" not in ua_lower:
            browser = "Google Chrome"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            browser = "Safari"
        elif "firefox" in ua_lower:
            browser = "Firefox"
        elif "edg" in ua_lower:
            browser = "Microsoft Edge"
        else:
            browser = "Unknown Browser"

        # Detect device
        if "mobile" in ua_lower or "android" in ua_lower:
            if "android" in ua_lower:
                device = "Android Device"
            elif "iphone" in ua_lower:
                device = "iPhone"
            else:
                device = "Mobile Device"
        elif "ipad" in ua_lower:
            device = "iPad"
        elif "mac" in ua_lower:
            device = "Mac"
        elif "windows" in ua_lower:
            device = "Windows PC"
        elif "linux" in ua_lower:
            device = "Linux"
        else:
            device = "Unknown Device"

        return {"browser": browser, "device": device}

    def _get_location_from_ip(self, ip_address: str) -> Optional[str]:
        """Get approximate location from IP address (optional feature)"""
        # This would require an IP geolocation service
        # For now, return None or implement with a service like ipapi.co
        try:
            import httpx

            response = httpx.get(f"https://ipapi.co/{ip_address}/json/", timeout=2)
            if response.status_code == 200:
                data = response.json()
                city = data.get("city", "")
                region = data.get("region", "")
                country = data.get("country_name", "")
                if city and country:
                    return f"{city}, {region}, {country}"
                elif country:
                    return country
        except:
            pass
        return None

    @staticmethod
    def send_vetting_form_invitation_email(
        to_email: str,
        applicant_name: str,
        service_type_name: str,
        reference_number: str,
        service_request_id: str,
        expires_at: datetime,
        applicant_id: str,
    ) -> bool:
        """Send vetting form invitation email"""

        form_url = (
            f"{settings.FRONTEND_URL}/vetting-form/{service_request_id}?applicant_id={applicant_id}"
        )

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 0;
                    background-color: #f4f4f4;
                }
                .email-container {
                    background: white;
                    margin: 20px;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }
                .content {
                    padding: 40px 30px;
                }
                .button {
                    display: inline-block;
                    padding: 15px 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white !important;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: 600;
                    font-size: 16px;
                }
                .info-box {
                    background: #f8f9fa;
                    padding: 20px;
                    border-left: 4px solid #667eea;
                    margin: 25px 0;
                    border-radius: 5px;
                }
                .warning {
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .footer {
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    font-size: 13px;
                    color: #666;
                    border-top: 1px solid #e0e0e0;
                }
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>📋 Vetting Form Invitation</h1>
                    <p>{{ service_type_name }}</p>
                </div>
                
                <div class="content">
                    <p>Dear <strong>{{ applicant_name }}</strong>,</p>
                    
                    <p>You have been invited to complete a background check vetting form for <strong>{{ service_type_name }}</strong>.</p>
                    
                    <div class="info-box">
                        <p><strong>Reference Number:</strong> {{ reference_number }}</p>
                        <p><strong>Service Type:</strong> {{ service_type_name }}</p>
                        <p><strong>Deadline:</strong> {{ expires_at }}</p>
                    </div>
                    
                    <p>Please click the button below to fill out the vetting form:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{ form_url }}" class="button">Complete Vetting Form</a>
                    </div>
                    
                    <div class="warning">
                        <p><strong>⏰ Important:</strong> This invitation will expire on {{ expires_at }}. Please complete the form before the deadline.</p>
                    </div>
                    
                    <p><strong>What you need to prepare:</strong></p>
                    <ul>
                        <li>Personal identification documents</li>
                        <li>Educational certificates</li>
                        <li>Employment history details</li>
                        <li>Reference contacts</li>
                    </ul>
                    
                    <p>If you have any questions, please contact the requesting organization.</p>
                </div>
                
                <div class="footer">
                    <p><strong>{{ app_name }}</strong></p>
                    <p>Background Checks & Clearance Investigations</p>
                </div>
            </div>
        </body>
        </html>
        """

        from jinja2 import Template

        template = Template(html_template)
        html_content = template.render(
            app_name=settings.APP_NAME,
            applicant_name=applicant_name,
            service_type_name=service_type_name,
            reference_number=reference_number,
            form_url=form_url,
            expires_at=expires_at.strftime("%B %d, %Y at %H:%M UTC"),
        )

        subject = f"Vetting Form Invitation - {service_type_name}"

        email_service = EmailService()
        return email_service.send_email(to_email, subject, html_content, None)
