# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import Role, Periodicity, SystemSetting

def seed_data():
    db = SessionLocal()
    try:
        # Seed Roles
        roles_to_seed = [
            {"code": "SYSTEM_ADMIN", "name": "System Administrator", "description": "Responsible for global platform administration."},
            {"code": "SURVEY_ADMIN", "name": "Survey Administrator", "description": "Responsible for survey operations."},
            {"code": "ACCOUNT_MANAGER", "name": "Account Manager", "description": "Responsible for company and contact management."},
            {"code": "COMPANY_CONTACT", "name": "Company Contact", "description": "Representative of a sampled company."}
        ]

        for role_data in roles_to_seed:
            existing = db.query(Role).filter(Role.code == role_data["code"]).first()
            if not existing:
                role = Role(**role_data)
                db.add(role)
                print(f"Added role: {role_data['code']}")

        # Seed Periodicities
        periodicities_to_seed = [
            {"code": "MONTHLY", "name": "Monthly"},
            {"code": "QUARTERLY", "name": "Quarterly"},
            {"code": "SEMESTRIAL", "name": "Semiannual/Semestrial"},
            {"code": "ANNUAL", "name": "Annual"},
            {"code": "BIENNIAL", "name": "Biennial"},
            {"code": "CUSTOM", "name": "Custom"}
        ]

        for per_data in periodicities_to_seed:
            existing = db.query(Periodicity).filter(Periodicity.code == per_data["code"]).first()
            if not existing:
                per = Periodicity(**per_data)
                db.add(per)
                print(f"Added periodicity: {per_data['code']}")

        # Seed System Settings
        settings_to_seed = [
            {"setting_key": "OTP_EXPIRATION_MINUTES", "setting_value": "5", "description": "OTP expiration duration in minutes"},
            {"setting_key": "MAX_LOGIN_ATTEMPTS", "setting_value": "3", "description": "Max failed login attempts before lock"},
            {"setting_key": "ACCOUNT_LOCK_HOURS", "setting_value": "24", "description": "Duration to lock account in hours"},
            {"setting_key": "PASSWORD_ONLY_DURATION_HOURS", "setting_value": "1", "description": "Duration of password-only login bypass"},
            {"setting_key": "DEFAULT_LANGUAGE", "setting_value": "fr", "description": "Default platform language"},
            {"setting_key": "EMAIL_PROVIDER", "setting_value": "brevo", "description": "Email delivery service provider"}
        ]

        for setting_data in settings_to_seed:
            existing = db.query(SystemSetting).filter(SystemSetting.setting_key == setting_data["setting_key"]).first()
            if not existing:
                setting = SystemSetting(**setting_data)
                db.add(setting)
                print(f"Added system setting: {setting_data['setting_key']}")

        db.commit()
        print("Seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
