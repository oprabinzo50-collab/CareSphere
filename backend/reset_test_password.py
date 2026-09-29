from app.database import SessionLocal
from app.models.user import User
from app.security.password import hash_password


USERNAME = "test_admin"
NEW_PASSWORD = "CareSphere@2026"


def main():
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.username == USERNAME)
            .first()
        )

        if user is None:
            print("Test user not found.")
            return

        user.password_hash = hash_password(NEW_PASSWORD)

        db.commit()

        print("Test user password reset successfully.")
        print("Username:", user.username)
        print("User ID:", user.id)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()