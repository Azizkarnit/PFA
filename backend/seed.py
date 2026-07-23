import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
import random
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models import (
    Role, User, Sector, Activity, Company, Contact, Survey, Periodicity, 
    SurveyQuestionnaire, SurveyAssignment, SystemSetting, AuditLog, 
    Notification, LoginAttempt, Sample, SampleCompany, SurveyPassage, 
    SurveyActivation, SurveyResultFile, CollectionTracking
)
# Drop all tables first to ensure a clean slate, then create
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

fake = Faker()
db = SessionLocal()

def seed_data():
    print("Seeding database...")
    
    # 1. Seed Roles
    roles = ["System Administrator", "Account Manager", "Survey Administrator", "Company Contact"]
    role_objects = []
    for r_name in roles:
        role = db.query(Role).filter(Role.name == r_name).first()
        if not role:
            role = Role(name=r_name, code=r_name.replace(" ", "_").upper()[:20])
            db.add(role)
            db.commit()
            db.refresh(role)
        role_objects.append(role)
    print("Roles seeded.")
    
    # 2. Seed Sectors and Activities
    sectors_data = ["Technology", "Agriculture", "Manufacturing", "Finance", "Healthcare"]
    sector_objects = []
    for s_name in sectors_data:
        sector = db.query(Sector).filter(Sector.name == s_name).first()
        if not sector:
            sector = Sector(name=s_name, code=s_name[:3].upper())
            db.add(sector)
            db.commit()
            db.refresh(sector)
        sector_objects.append(sector)

    activities_data = ["Software Development", "Crop Farming", "Automotive", "Banking", "Hospital"]
    activity_objects = []
    for i, a_name in enumerate(activities_data):
        activity = db.query(Activity).filter(Activity.name == a_name).first()
        if not activity:
            activity = Activity(name=a_name, code=a_name[:3].upper(), sector_id=sector_objects[i].id)
            db.add(activity)
            db.commit()
            db.refresh(activity)
        activity_objects.append(activity)
    print("Sectors and Activities seeded.")
    
    # 3. Seed Companies
    print("Seeding Companies...")
    companies = []
    for _ in range(50):
        company = Company(
            identifier=str(fake.unique.random_number(digits=8, fix_len=True)),
            company_name=fake.company(),
            tax_number=str(fake.unique.random_number(digits=10, fix_len=True)),
            sector_id=random.choice(sector_objects).id,
            activity_id=random.choice(activity_objects).id,
            address=fake.address(),
            governorate=fake.state(),
            postal_code=fake.postcode(),
            phone=fake.phone_number()[:20],
            email=fake.company_email(),
            status=random.choice(["ACTIVE", "INACTIVE"])
        )
        db.add(company)
        companies.append(company)
    db.commit()

    # 4. Seed Internal Users (Admins, Account Managers)
    print("Seeding Internal Users...")
    hashed_pwd = get_password_hash("Password123!")
    
    internal_roles = role_objects[:3] # Admins, Account Managers, Survey Admins
    for _ in range(40):
        role = random.choice(internal_roles)
        user = User(
            role_id=role.id,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            password_hash=hashed_pwd,
            phone_number=fake.phone_number()[:20],
            status=random.choice(["ACTIVE", "ACTIVE", "ACTIVE", "LOCKED", "DISABLED"]),
            preferred_language=random.choice(["en", "fr", "ar"])
        )
        db.add(user)
    db.commit()

    # 5. Seed Contacts (External Users + Contact association)
    print("Seeding Contacts...")
    contact_role = role_objects[3]
    for comp in companies:
        for _ in range(random.randint(1, 3)):
            user = User(
                role_id=contact_role.id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.unique.email(),
                password_hash=hashed_pwd,
                phone_number=fake.phone_number()[:20],
                status="ACTIVE"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            contact = Contact(
                user_id=user.id,
                company_id=comp.id,
                position=fake.job(),
                is_primary_contact=random.choice([True, False])
            )
            db.add(contact)
    db.commit()
    
    # 6. Seed Periodicity
    print("Seeding Periodicities...")
    periodicities = []
    for code, name in [("ANN", "Annuelle"), ("MEN", "Mensuelle"), ("TRI", "Trimestrielle")]:
        p = db.query(Periodicity).filter(Periodicity.code == code).first()
        if not p:
            p = Periodicity(code=code, name=name)
            db.add(p)
            db.commit()
            db.refresh(p)
        periodicities.append(p)

    # 7. Seed Surveys
    print("Seeding Surveys and related entities...")
    admin_user = db.query(User).filter(User.role_id == role_objects[0].id).first()
    surveys = []
    for _ in range(10):
        survey = Survey(
            code=f"SRV-{fake.unique.random_number(digits=4)}",
            name=fake.catch_phrase(),
            description=fake.text(),
            periodicity_id=random.choice(periodicities).id,
            created_by=admin_user.id if admin_user else 1,
            status=random.choice(["ACTIVE", "INACTIVE"])
        )
        db.add(survey)
        surveys.append(survey)
    db.commit()

    # 8. Seed Survey related entities
    print("Seeding Survey details (Questionnaires, Assignments, Passages, etc.)...")
    for survey in surveys:
        # Assignments
        for _ in range(random.randint(2, 5)):
            contact_user = db.query(User).filter(User.role_id == role_objects[3].id).first()
            if contact_user:
                a = SurveyAssignment(
                    survey_id=survey.id,
                    user_id=contact_user.id
                )
                db.add(a)

        # Passage and Activation
        passage = SurveyPassage(
            survey_id=survey.id,
            year=2024,
            passage_number=random.randint(1, 12),
            opening_date=fake.date_time_this_year(),
            closing_date=fake.date_time_this_year(),
            status="OPEN"
        )
        db.add(passage)
        db.commit()
        db.refresh(passage)
        
        # Questionnaire
        q = SurveyQuestionnaire(
            passage_id=passage.id,
            questionnaire_url=f"http://example.com/q/{survey.code}",
            questionnaire_pdf_path=f"/uploads/questionnaires/{survey.code}.pdf",
            version="1.0",
            status="ACTIVE"
        )
        db.add(q)
        
        # Activation table might not exist or be needed if SurveyPassage has activated_by. Let's wrap it in try.
        try:
            activation = SurveyActivation(
                survey_id=survey.id,
                passage_id=passage.id,
                start_date=fake.date_time_this_year(),
                end_date=fake.date_time_this_year(),
                is_active=True,
                activated_by=admin_user.id if admin_user else 1
            )
            db.add(activation)
        except Exception:
            pass
        
        # Survey Result & Collection Tracking
        assigned_companies = [c for c in companies if random.choice([True, False])]
        for comp in assigned_companies[:3]:
            try:
                result = SurveyResultFile(
                    passage_id=passage.id,
                    company_id=comp.id,
                    uploaded_by=admin_user.id if admin_user else 1,
                    filename=f"result_{comp.id}.pdf",
                    file_path=f"/uploads/results/result_{comp.id}.pdf",
                    status="VALIDATED"
                )
                db.add(result)
            except Exception:
                pass
            
            try:
                tracking = CollectionTracking(
                    passage_id=passage.id,
                    company_id=comp.id,
                    status="COMPLETED"
                )
                db.add(tracking)
            except Exception:
                pass

    # 9. Seed System Settings
    print("Seeding System Settings...")
    try:
        settings = [
            SystemSetting(setting_key="MAINTENANCE_MODE", setting_value="false", description="System in maintenance"),
            SystemSetting(setting_key="MAX_LOGIN_ATTEMPTS", setting_value="5", description="Max failed logins")
        ]
        for s in settings:
            db.add(s)
    except Exception:
        pass

    # 10. Seed Logs, Notifications, Login Attempts
    print("Seeding Logs and Notifications...")
    try:
        for user in db.query(User).limit(10).all():
            db.add(AuditLog(user_id=user.id, action="LOGIN", entity_type="USER", entity_id=user.id, ip_address=fake.ipv4()))
            db.add(AuditLog(user_id=user.id, action="UPDATE_PROFILE", entity_type="USER", entity_id=user.id, ip_address=fake.ipv4()))
            db.add(Notification(user_id=user.id, channel="EMAIL", type="INVITATION", recipient=user.email, status="SENT"))
            db.add(LoginAttempt(user_id=user.id, ip_address=fake.ipv4(), user_agent=fake.user_agent(), success=True))
        db.commit()
    except Exception as e:
        print(f"Error seeding logs: {e}")
        db.rollback()

    # 11. Seed Samples
    print("Seeding Samples...")
    try:
        # Get a passage for the sample
        sample_passage = db.query(SurveyPassage).first()
        if sample_passage:
            for _ in range(3):
                sample = Sample(name=fake.word(), description=fake.sentence(), passage_id=sample_passage.id, created_by=admin_user.id if admin_user else 1)
                db.add(sample)
                db.commit()
                db.refresh(sample)
                
                for comp in random.sample(companies, min(5, len(companies))):
                    db.add(SampleCompany(sample_id=sample.id, company_id=comp.id))
    except Exception:
        pass

    db.commit()
    print("Seeding complete! All tables have been populated with dynamic data.")

if __name__ == "__main__":
    try:
        seed_data()
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()
