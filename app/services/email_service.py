"""Email service layer for sending password recovery messages."""

import resend
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from app.core.config import Config

logger = logging.getLogger(__name__)


class MailService:
    """Service to handle constructing and sending system emails."""

    @staticmethod
    def send_password_recovery_email(email: str, raw_token: str, lang: str = "en") -> None:
        """Construct and dispatch a password recovery link to the user's email address."""
        # Generate the recovery URL linking back to the frontend page
        reset_url = f"{Config.FRONTEND_URL.rstrip('/')}/reset-password?token={raw_token}"

        # Select the template and subject line based on the user's active client language
        if lang == "es":
            subject = "Restablece tu contraseña de Orbit"
            html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Restablecer Contraseña de Orbit</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 20px; margin: 0;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; padding: 30px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid #334155;">
        <div style="text-align: center; margin-bottom: 24px;">
            <span style="font-size: 24px; font-weight: bold; color: #3b82f6;">Orbit</span>
        </div>
        <h2 style="font-size: 20px; font-weight: 600; text-align: center; margin-bottom: 16px; color: #ffffff;">Solicitud de Restablecimiento de Contraseña</h2>
        <p style="font-size: 15px; line-height: 1.6; color: #94a3b8; margin-bottom: 24px; text-align: center;">
            Has solicitado restablecer la contraseña de tu cuenta de Orbit. Haz clic en el botón de abajo para establecer una nueva contraseña. Este enlace es válido por 15 minutos.
        </p>
        <div style="text-align: center; margin-bottom: 24px;">
            <a href="{reset_url}" style="background-color: #3b82f6; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">Restablecer Contraseña</a>
        </div>
        <p style="font-size: 13px; line-height: 1.5; color: #64748b; text-align: center;">
            Si no solicitaste restablecer tu contraseña, por favor ignora este correo.
        </p>
        <hr style="border: 0; border-top: 1px solid #334155; margin: 24px 0;">
        <p style="font-size: 11px; line-height: 1.4; color: #475569; text-align: center;">
            Si el botón no funciona, copia y pega esta dirección URL en tu navegador:<br>
            <a href="{reset_url}" style="color: #3b82f6; text-decoration: none;">{reset_url}</a>
        </p>
    </div>
</body>
</html>
"""
        else:
            subject = "Reset your Orbit Password"
            html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Orbit Password Reset</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 20px; margin: 0;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; padding: 30px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid #334155;">
        <div style="text-align: center; margin-bottom: 24px;">
            <span style="font-size: 24px; font-weight: bold; color: #3b82f6;">Orbit</span>
        </div>
        <h2 style="font-size: 20px; font-weight: 600; text-align: center; margin-bottom: 16px; color: #ffffff;">Password Reset Request</h2>
        <p style="font-size: 15px; line-height: 1.6; color: #94a3b8; margin-bottom: 24px; text-align: center;">
            You requested to reset your password for your Orbit account. Click the button below to set a new password. This link is valid for 15 minutes.
        </p>
        <div style="text-align: center; margin-bottom: 24px;">
            <a href="{reset_url}" style="background-color: #3b82f6; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">Reset Password</a>
        </div>
        <p style="font-size: 13px; line-height: 1.5; color: #64748b; text-align: center;">
            If you did not request a password reset, please ignore this email.
        </p>
        <hr style="border: 0; border-top: 1px solid #334155; margin: 24px 0;">
        <p style="font-size: 11px; line-height: 1.4; color: #475569; text-align: center;">
            If the button doesn't work, copy and paste this URL into your browser:<br>
            <a href="{reset_url}" style="color: #3b82f6; text-decoration: none;">{reset_url}</a>
        </p>
    </div>
</body>
</html>
"""

        resend.api_key = Config.SMTP_API_KEY

        r = resend.Emails.send({
            "from": "orbit@redorbit.win",
            "to": email,
            "subject": subject,
            "html": html_body
        })

    @staticmethod
    def send_announcement_email(email: str, subject: str, body_content: str) -> None:
        """Construct and dispatch an announcement/notification email."""
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{subject}</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 20px; margin: 0;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 12px; padding: 30px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid #334155;">
        <div style="text-align: center; margin-bottom: 24px;">
            <span style="font-size: 24px; font-weight: bold; color: #ec4899;">Orbit Announcement</span>
        </div>
        <h2 style="font-size: 20px; font-weight: 600; text-align: center; margin-bottom: 16px; color: #ffffff;">{subject}</h2>
        <div style="font-size: 15px; line-height: 1.6; color: #94a3b8; margin-bottom: 24px; text-align: left; white-space: pre-line;">
            {body_content}
        </div>
        <hr style="border: 0; border-top: 1px solid #334155; margin: 24px 0;">
        <p style="font-size: 11px; line-height: 1.4; color: #475569; text-align: center;">
            This is an official system announcement from the Orbit platform.
        </p>
    </div>
</body>
</html>
"""

        resend.api_key = Config.SMTP_API_KEY

        r = resend.Emails.send({
            "from": "orbit@redorbit.win",
            "to": email,
            "subject": subject,
            "html": html_body
        })
        
        """  # Check if SMTP is configured
        if not Config.SMTP_HOST:
            print("\n" + "="*80)
            print(f"SMTP NOT CONFIGURED. MOCK EMAIL DETAILS FOR {email} ({lang.upper()}):")
            print(f"Subject: {subject}")
            print(f"Recovery link: {reset_url}")
            print("="*80 + "\n")
            logger.info("Mock recovery email logged to console for %s", email)
            return

        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = Config.SMTP_FROM
            msg['To'] = email

            # Attach HTML part
            msg.attach(MIMEText(html_body, 'html'))

            # Connect and send
            # TLS Connection (port 587)
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.ehlo()

            # Authenticate if credentials are provided
            if Config.SMTP_USERNAME and Config.SMTP_PASSWORD:
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)

            server.sendmail(Config.SMTP_FROM, [email], msg.as_string())
            server.quit()
            logger.info("Recovery email sent successfully to %s", email)
        except Exception as e:
            logger.error("Failed to send recovery email to %s: %s", email, str(e))
            # Even if real SMTP fails, log link to stdout as safety fallback
            print(f"\n[FALLBACK EMAIL LOG] Recovery URL: {reset_url}\n") """
