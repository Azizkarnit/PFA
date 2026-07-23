"""
Script to create a test System Admin user for development.
Run once: venv\Scripts\python create_admin.py
"""
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User, Role

def create_admin():
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.code == "SYSTEM_ADMINISTRATOR").first()
        if not role:
            print("ERROR: SYSTEM_ADMINISTRATOR role not found. Run seed.py first.")
            return

        existing = db.query(User).filter(User.email == "admin@ins.tn").first()
        if existing:
            print("Admin user already exists: admin@ins.tn")
            return

        admin = User(
            role_id=role.id,
            email="admin@ins.tn",
            first_name="System",
            last_name="Admin",
            password_hash=get_password_hash("Admin@123"),
            first_login=False,
            status="ACTIVE",
            preferred_language="fr",
            email_verified=True,
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully!")
        print("   Email:    admin@ins.tn")
        print("   Password: Admin@123")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
