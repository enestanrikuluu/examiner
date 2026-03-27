"""Create the initial admin user for a fresh deployment."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from passlib.hash import bcrypt
from sqlalchemy import select

from src.core.database import async_session_factory, engine
from src.users.models import User


async def create_admin_user(
    email: str,
    password: str,
    full_name: str = "Admin",
) -> None:
    async with async_session_factory() as db:
        existing = await db.execute(
            select(User).where(User.email == email)
        )
        if existing.scalar_one_or_none():
            print(f"Admin user '{email}' already exists. Skipping.")
            return

        hashed = bcrypt.using(rounds=12).hash(password)
        admin = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed,
            role="admin",
            is_active=True,
            auth_provider="local",
        )
        db.add(admin)
        await db.commit()
        print(f"Admin user '{email}' created successfully.")

    await engine.dispose()


def main() -> None:
    email = os.getenv("ADMIN_EMAIL", "admin@examiner.local")
    password = os.getenv("ADMIN_PASSWORD")

    if not password:
        print("Error: ADMIN_PASSWORD environment variable is required.")
        print("Usage: ADMIN_PASSWORD=yourpassword python scripts/seed_admin.py")
        sys.exit(1)

    asyncio.run(create_admin_user(email, password))


if __name__ == "__main__":
    main()
