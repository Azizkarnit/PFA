from app.core.celery_app import celery_app
from app.core.config import settings
import logging
# pyrefly: ignore [missing-import]
import requests

logger = logging.getLogger(__name__)

def send_via_brevo(to_email: str, subject: str, html_content: str) -> dict:
    """Helper to send transactional email via Brevo API.
    
    Returns a dict with 'status': 'sent' on success or 'no_key' if API key is missing.
    Raises an exception on API failure so the caller can handle it.
    """
    if not settings.BREVO_API_KEY:
        logger.warning("BREVO_API_KEY is not set. Email not sent via Brevo.")
        return {"status": "no_key"}
        
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME,
            "email": settings.BREVO_SENDER_EMAIL
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        # Parse error body before raising so we can log it
        if not response.ok:
            error_body = ""
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            logger.error(f"Brevo API error {response.status_code}: {error_body}")
            print(f"[EMAIL ERROR] Brevo rejected the email to {to_email}: {error_body}")
            raise Exception(f"Brevo API error {response.status_code}: {error_body}")
        logger.info(f"Email successfully sent via Brevo to {to_email}")
        print(f"[EMAIL OK] OTP email successfully delivered to {to_email} via Brevo.")
        return {"status": "sent", "response": response.json()}
    except Exception:
        raise

@celery_app.task
def send_otp_email(to_email: str, otp_code: str, language: str = "fr"):
    """
    Sends the OTP code to the user.
    """
    dispatch_msg = f"""
========== EMAIL DISPATCH ==========
To: {to_email}
Language: {language}
Subject: Your Login Verification Code
Body: Your INS Portal code is: {otp_code}
=====================================
"""
    logger.info(dispatch_msg)
    print(dispatch_msg)

    # Select language template
    if language == "ar":
        subject = "رمز التحقق لمنصة المعهد الوطني للإحصاء"
        html = f"""
        <div dir="rtl" style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1e3a8a;">رمز التحقق الخاص بك</h2>
            <p style="font-size: 16px; color: #4b5563;">الرجاء استخدام الرمز التالي لتسجيل الدخول إلى حسابك. هذا الرمز صالح لمدة 5 دقائق:</p>
            <div style="font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 4px; padding: 15px; background-color: #f3f4f6; border-radius: 6px; display: inline-block; margin: 20px 0;">
                {otp_code}
            </div>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">إذا لم تطلب هذا الرمز، يرجى تجاهل هذا البريد الإلكتروني.</p>
        </div>
        """
    elif language == "en":
        subject = "Your INS Portal Verification Code"
        html = f"""
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1e3a8a;">Your Verification Code</h2>
            <p style="font-size: 16px; color: #4b5563;">Please use the following code to log in to your account. This code is valid for 5 minutes:</p>
            <div style="font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 4px; padding: 15px; background-color: #f3f4f6; border-radius: 6px; display: inline-block; margin: 20px 0;">
                {otp_code}
            </div>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">If you did not request this code, please ignore this email.</p>
        </div>
        """
    else:  # Default to 'fr'
        subject = "Votre code de vérification INS"
        html = f"""
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1e3a8a;">Votre code de vérification</h2>
            <p style="font-size: 16px; color: #4b5563;">Veuillez utiliser le code suivant pour vous connecter à votre compte. Ce code est valide pendant 5 minutes :</p>
            <div style="font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 4px; padding: 15px; background-color: #f3f4f6; border-radius: 6px; display: inline-block; margin: 20px 0;">
                {otp_code}
            </div>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">Si vous n'avez pas demandé ce code, vous pouvez ignorer cet e-mail en toute sécurité.</p>
        </div>
        """

    try:
        res = send_via_brevo(to_email, subject, html)
        email_sent = res.get("status") == "sent"
    except Exception as e:
        email_sent = False
        logger.error(f"OTP email delivery failed for {to_email}: {e}")
        print(f"[EMAIL FAILED] Could not deliver OTP email to {to_email}: {e}")
    return {"status": "processed", "email_sent": email_sent, "to": to_email}

@celery_app.task
def send_password_reset_email(to_email: str, reset_link: str, language: str = "fr"):
    """
    Sends the password reset link to the user.
    """
    dispatch_msg = f"""
========== EMAIL DISPATCH ==========
To: {to_email}
Language: {language}
Subject: Reset Your Password
Body: Click here to reset your password: {reset_link}
=====================================
"""
    logger.info(dispatch_msg)
    print(dispatch_msg)

    if language == "ar":
        subject = "إعادة تعيين كلمة المرور الخاصة بك"
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin: 0; padding: 20px;">
        <div dir="rtl" style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1e3a8a;">إعادة تعيين كلمة المرور</h2>
            <p style="font-size: 16px; color: #4b5563;">لتغيير كلمة المرور الخاصة بك، يرجى الضغط على الرابط التالي:</p>
            <p><a href="{reset_link}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">إعادة تعيين كلمة المرور</a></p>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">إذا لم تطلب هذا، يرجى تجاهل هذا البريد.</p>
        </div>
        </body>
        </html>
        """
    elif language == "en":
        subject = "Reset Your Password"
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin: 0; padding: 20px;">
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1e3a8a;">Reset Your Password</h2>
            <p style="font-size: 16px; color: #4b5563;">To reset your password, please click the link below:</p>
            <p><a href="{reset_link}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">Reset Password</a></p>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">If you did not request this, you can ignore this email.</p>
        </div>
        </body>
        </html>
        """
    else:  # Default to 'fr'
        subject = "Réinitialiser votre mot de passe"
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin: 0; padding: 20px;">
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1e3a8a;">Réinitialiser votre mot de passe</h2>
            <p style="font-size: 16px; color: #4b5563;">Pour réinitialiser votre mot de passe, veuillez cliquer sur le lien ci-dessous :</p>
            <p><a href="{reset_link}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">Réinitialiser le mot de passe</a></p>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet e-mail.</p>
        </div>
        </body>
        </html>
        """

    res = send_via_brevo(to_email, subject, html)
    return {"status": "processed", "brevo_result": res, "to": to_email}
