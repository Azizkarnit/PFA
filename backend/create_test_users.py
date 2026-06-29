from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import User, Role

def create_test_users():
    db = SessionLocal()
    try:
        # Define the roles and emails we want to create
        test_users = [
            {"email": "azizkarnit@gmail.com", "role_code": "COMPANY_CONTACT"}
        ]

        for u in test_users:
            role = db.query(Role).filter(Role.code == u["role_code"]).first()
            if not role:
                print(f"ERROR: {u['role_code']} role not found. Run seed.py first.")
                continue

            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                print(f"User already exists: {u['email']}")
                continue

            new_user = User(
                role_id=role.id,
                email=u["email"],
                password_hash=get_password_hash("Test@123"),
                first_login=True,
                status="ACTIVE",
                preferred_language="fr",
                email_verified=True,
            )
            db.add(new_user)
            print(f"Created test user: {u['email']} (Role: {u['role_code']})")

        db.commit()
        print("\nAll test users created successfully!")
        print("Default Password for all test users: Test@123")
        print("Note: They all have first_login=True to test the first login flow.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
