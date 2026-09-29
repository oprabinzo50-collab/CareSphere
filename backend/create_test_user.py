from app.database import SessionLocal
from app.models.user import User
from datetime import datetime, timezone

from app.security.password import hash_password


USERNAME = "test_admin"
PASSWORD = "CareSphere@2026"
FULL_NAME = "CareSphere Test Admin"
ROLE = "administrator"


def main():
    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.username == USERNAME)
            .first()
        )

        if existing_user:
            print("Test user already exists.")
            print("Username:", existing_user.username)
            print("User ID:", existing_user.id)
            return

        user = User(
            username=USERNAME,
            password_hash=hash_password(PASSWORD),
            full_name=FULL_NAME,
            role=ROLE,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_login_at=None,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("Test user created successfully.")
        print("User ID:", user.id)
        print("Username:", user.username)
        print("Role:", user.role)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()