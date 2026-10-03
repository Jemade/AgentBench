import os
import uuid
from sqlalchemy import select, insert
from .db import transaction, users, initialize
from .security import password_hash


def main():
    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not email or "@" not in email or len(password) < 12:
        raise SystemExit("Set ADMIN_EMAIL and ADMIN_PASSWORD (at least 12 characters)")
    initialize()
    with transaction() as c:
        if c.execute(select(users.c.id).where(users.c.email == email)).first():
            print("Account already exists; no changes made.")
            return
        c.execute(
            insert(users).values(
                id=uuid.uuid4().hex,
                email=email,
                name=os.getenv("ADMIN_NAME", "Jayden Mapasure"),
                password=password_hash(password),
            )
        )
    print("Account created. No fabricated evaluation results added.")


if __name__ == "__main__":
    main()
