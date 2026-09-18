"""Set the dashboard administrator's email and password.

Usage (from the backend folder):

    venv/Scripts/python.exe scripts/set_admin_password.py <email> [database-url]

Without a database URL the local database from .env is used. Pass the Railway
tunnel URL to update the deployed database instead. The password is read from
the ADMIN_NEW_PASSWORD environment variable, or typed in when prompted, so it
never ends up in the shell history.
"""

import getpass
import os
import sys

from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User  # noqa: E402
from app.routers.auth import hash_password  # noqa: E402


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: set_admin_password.py <email> [database-url]")

    email = sys.argv[1].strip().lower()
    url = sys.argv[2] if len(sys.argv) > 2 else dotenv_values(".env").get("DATABASE_URL")

    if not url:
        sys.exit("No database URL given and DATABASE_URL is missing from .env")

    password = os.getenv("ADMIN_NEW_PASSWORD") or getpass.getpass("New password: ")
    if len(password) < 8:
        sys.exit("Password must be at least 8 characters")

    engine = create_engine(url)
    session = sessionmaker(bind=engine)()

    try:
        user = session.query(User).filter(User.email == email).first()

        if user is None:
            # Reuse the existing administrator account if there is one, so the
            # dashboard does not end up with two logins.
            user = session.query(User).order_by(User.id).first()

        if user is None:
            user = User(email=email, full_name="IFDC Administrator", role="System Administrator",
                        password_hash=hash_password(password))
            session.add(user)
            action = "created"
        else:
            user.email = email
            user.password_hash = hash_password(password)
            user.is_active = True
            action = "updated"

        session.commit()
        print(f"Administrator {action}: {email}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
