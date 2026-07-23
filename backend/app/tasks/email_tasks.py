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
        if not response.ok:
            error_body = ""
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            logger.error(f"Brevo API error {response.status_code}: {error_body}")
            raise Exception(f"Brevo API error {response.status_code}: {error_body}")
        logger.info(f"Email successfully sent via Brevo to {to_email}")
        return {"status": "sent", "response": response.json()}
    except Exception:
        raise


def send_otp_email(to_email: str, otp_code: str, language: str = "fr", expiration_minutes: int = 5) -> dict:
    """
    Sends the OTP code to the user.
    Plain synchronous function — called directly from API routes (not via Celery).
    The expiration_minutes parameter is rendered in the email body so it stays
    in sync with whatever value is configured in System Settings.
    """
    dispatch_msg = (
        f"\n========== EMAIL DISPATCH ==========\n"
        f"To: {to_email}\n"
        f"Language: {language}\n"
        f"Subject: OTP Code\n"
        f"Body: Your INS Portal code is: {otp_code}\n"
        f"====================================="
    )
    logger.info(dispatch_msg)
    print(dispatch_msg, flush=True)

    if language == "ar":
        subject = "رمز التحقق لمنصة المعهد الوطني للإحصاء"
        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <body style="margin: 0; padding: 20px; direction: rtl; text-align: right;">
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1e3a8a;">رمز التحقق الخاص بك</h2>
            <p style="font-size: 16px; color: #4b5563;">الرجاء استخدام الرمز التالي لتسجيل الدخول إلى حسابك. هذا الرمز صالح لمدة {expiration_minutes} دقائق:</p>
            <div style="font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 4px; padding: 15px; background-color: #f3f4f6; border-radius: 6px; display: inline-block; margin: 20px 0; direction: ltr;">
                {otp_code}
            </div>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">إذا لم تطلب هذا الرمز، يرجى تجاهل هذا البريد الإلكتروني.</p>
        </div>
        </body>
        </html>
        """
    elif language == "en":
        subject = "Your INS Portal Verification Code"
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <body style="margin: 0; padding: 20px;">
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1e3a8a;">Your Verification Code</h2>
            <p style="font-size: 16px; color: #4b5563;">Please use the following code to log in to your account. This code is valid for {expiration_minutes} minutes:</p>
            <div style="font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 4px; padding: 15px; background-color: #f3f4f6; border-radius: 6px; display: inline-block; margin: 20px 0;">
                {otp_code}
            </div>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">If you did not request this code, please ignore this email.</p>
        </div>
        </body>
        </html>
        """
    else:  # Default to 'fr'
        subject = "Votre code de vérification INS"
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <body style="margin: 0; padding: 20px;">
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
            <h2 style="color: #1e3a8a;">Votre code de vérification</h2>
            <p style="font-size: 16px; color: #4b5563;">Veuillez utiliser le code suivant pour vous connecter à votre compte. Ce code est valide pendant {expiration_minutes} minutes :</p>
            <div style="font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 4px; padding: 15px; background-color: #f3f4f6; border-radius: 6px; display: inline-block; margin: 20px 0;">
                {otp_code}
            </div>
            <p style="font-size: 12px; color: #9ca3af; margin-top: 20px;">Si vous n'avez pas demandé ce code, vous pouvez ignorer cet e-mail en toute sécurité.</p>
        </div>
        </body>
        </html>
        """

    try:
        res = send_via_brevo(to_email, subject, html)
        email_sent = res.get("status") == "sent"
    except Exception as e:
        email_sent = False
        logger.error(f"OTP email delivery failed for {to_email}: {e}")
        print(f"[EMAIL FAILED] Could not deliver OTP email to {to_email}: {e}")
    return {"status": "processed", "email_sent": email_sent, "to": to_email}


def send_password_reset_email(to_email: str, reset_link: str, language: str = "fr") -> dict:
    """
    Sends the password reset link to the user.
    Plain synchronous function — called directly from API routes.
    """
    dispatch_msg = (
        f"\n========== EMAIL DISPATCH ==========\n"
        f"To: {to_email}\n"
        f"Language: {language}\n"
        f"Subject: Reset Your Password\n"
        f"Body: Click here to reset your password: {reset_link}\n"
        f"====================================="
    )
    logger.info(dispatch_msg)
    print(dispatch_msg, flush=True)

    if language == "ar":
        subject = "إعادة تعيين كلمة المرور الخاصة بك"
        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <body style="margin: 0; padding: 20px; direction: rtl; text-align: right;">
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 8px; max-width: 500px; margin: 0 auto;">
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
        <html lang="en">
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
        <html lang="fr">
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

    try:
        res = send_via_brevo(to_email, subject, html)
        return {"status": "processed", "email_sent": res.get("status") == "sent", "to": to_email}
    except Exception as e:
        logger.error(f"Password reset email failed for {to_email}: {e}")
        return {"status": "processed", "email_sent": False, "to": to_email}


import secrets
import string
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.survey_passage import SurveyPassage
from app.models.survey_questionnaire import SurveyQuestionnaire
from app.models.survey import Survey
from app.models.sample import Sample
from app.models.sample_company import SampleCompany
from app.models.company import Company
from app.models.contact import Contact
from app.models.user import User
from app.models.role import Role
from app.models.questionnaire_token import QuestionnaireToken
from app.core.security import get_password_hash


def generate_random_password(length=8):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for i in range(length))


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_survey_invitations(self, passage_id: int, frontend_url: str | None = None):
    """
    Celery task that emails survey invitations to all companies in a passage's sample.
    Retries up to 3 times with a 60-second delay on failure.
    """
    if frontend_url is None:
        frontend_url = settings.FRONTEND_URL

    db: Session = SessionLocal()
    try:
        passage = db.query(SurveyPassage).filter(SurveyPassage.id == passage_id).first()
        if not passage:
            return

        survey = db.query(Survey).filter(Survey.id == passage.survey_id).first()
        questionnaire = (
            db.query(SurveyQuestionnaire)
            .filter(SurveyQuestionnaire.passage_id == passage_id)
            .order_by(SurveyQuestionnaire.id.desc())
            .first()
        )

        if not survey or not questionnaire:
            return

        q_url = questionnaire.questionnaire_url or ""
        q_pdf = ""
        if questionnaire.questionnaire_pdf_path:
            filename = questionnaire.questionnaire_pdf_path.split('/')[-1]
            # Use BACKEND_URL from config instead of fragile string replacement
            q_pdf = f"{settings.BACKEND_URL}{settings.API_V1_STR}/surveys/downloads/questionnaire/{filename}"

        sample = db.query(Sample).filter(Sample.passage_id == passage_id).order_by(Sample.id.desc()).first()
        if not sample:
            return

        sample_companies = db.query(SampleCompany).filter(SampleCompany.sample_id == sample.id).all()
        contact_role = db.query(Role).filter(Role.code == "COMPANY_CONTACT").first()
        if not contact_role:
            return

        for sc in sample_companies:
            company = db.query(Company).filter(Company.id == sc.company_id).first()
            if not company:
                continue

            primary_contact = db.query(Contact).filter(
                Contact.company_id == company.id,
                Contact.is_primary_contact == True,
                Contact.status == "ACTIVE"
            ).first()

            user = None
            contact_to_use = None
            generated_password = None
            if primary_contact:
                user = db.query(User).filter(User.id == primary_contact.user_id).first()
                contact_to_use = primary_contact
            elif company.email:
                user = db.query(User).filter(User.email == company.email).first()
                if not user:
                    generated_password = generate_random_password()
                    user = User(
                        email=company.email,
                        first_name=company.company_name,
                        last_name="Contact",
                        password_hash=get_password_hash(generated_password),
                        role_id=contact_role.id,
                        status="ACTIVE",
                        first_login=True
                    )
                    db.add(user)
                    db.flush()

                    contact_to_use = Contact(
                        user_id=user.id,
                        company_id=company.id,
                        is_primary_contact=True,
                        status="ACTIVE"
                    )
                    db.add(contact_to_use)
                    db.commit()
                    db.refresh(user)
                else:
                    contact_to_use = Contact(
                        user_id=user.id,
                        company_id=company.id,
                        is_primary_contact=True,
                        status="ACTIVE"
                    )
                    db.add(contact_to_use)
                    db.commit()

            if not user or not user.email or not contact_to_use:
                continue

            # Generate stable UUID link token for this contact and passage
            token_obj = db.query(QuestionnaireToken).filter(
                QuestionnaireToken.contact_id == contact_to_use.id,
                QuestionnaireToken.passage_id == passage_id
            ).first()

            if not token_obj:
                import uuid as _uuid
                token_uuid = str(_uuid.uuid4())
                token_obj = QuestionnaireToken(
                    token=token_uuid,
                    contact_id=contact_to_use.id,
                    company_id=company.id,
                    passage_id=passage_id
                )
                db.add(token_obj)
                db.commit()
                db.refresh(token_obj)

            ext_survey_link = f"{settings.EXT_APP_URL}/?uuid={token_obj.token}"
                
            # Send in-app notification
            from app.core.notification_service import create_notification
            create_notification(
                db,
                user.id,
                "New Survey Passage",
                f"Your company has been selected for the survey '{survey.name}'. Passage {passage.year}/P{passage.passage_number} is now open.",
                type="INFO",
                action_url=f"/portal/survey/{survey.id}"
            )

            subject = f"Invitation: {survey.name}"
            html = f'''
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    @media only screen and (max-width: 600px) {{
                        .action-btn {{
                            display: block !important;
                            width: 100% !important;
                            box-sizing: border-box !important;
                            margin-right: 0 !important;
                            margin-bottom: 10px !important;
                        }}
                    }}
                </style>
            </head>
            <body style="margin: 0; padding: 20px; font-family: Arial, sans-serif;">
            <div style="border: 1px solid #eee; border-radius: 8px; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1e3a8a;">Invitation à l\'enquête : {survey.name}</h2>
                <p>Bonjour,</p>
                <p>Vous êtes invité à participer à l\'enquête <strong>{survey.name}</strong> organisée par l\'Institut National de la Statistique.</p>
            '''
            if generated_password:
                html += f'''
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin:0 0 10px 0;"><strong>Vos identifiants de connexion :</strong></p>
                    <p style="margin:0;">Email: <strong>{user.email}</strong></p>
                    <p style="margin:0;">Mot de passe: <strong>{generated_password}</strong></p>
                </div>
                '''

            html += '''
                <p>Veuillez vous connecter au portail pour consulter et remplir votre questionnaire :</p>
                <div style="margin-top: 15px;">
            '''

            html += f'''
                    <a href="{frontend_url}/login" class="action-btn" style="background-color: #2563eb; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; display: inline-block; text-align: center; margin-right: 10px; margin-bottom: 10px; font-weight: bold;">Accéder au portail INS</a>
                </div>
            '''

            html += '''
                <br>
                <p>Cordialement,<br>L\'équipe INS</p>
            </div>
            </body>
            </html>
            '''

            try:
                send_via_brevo(str(user.email), subject, html)
                logger.info(f"Survey invitation sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send survey invitation to {user.email}: {e}")

    except Exception as e:
        logger.error(f"Error in send_survey_invitations task: {e}")
        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for send_survey_invitations (passage_id={passage_id})")
    finally:
        db.close()
