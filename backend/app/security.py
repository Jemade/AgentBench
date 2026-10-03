import hashlib
import hmac
import secrets
from fastapi import Request, HTTPException
from sqlalchemy import select
from .db import engine, users, sessions, now


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password):
    salt = secrets.token_hex(16)
    return (
        salt + ":" + hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    )


def password_matches(password, encoded):
    salt, expected = encoded.split(":")
    return hmac.compare_digest(
        hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex(), expected
    )


def current_user(request: Request):
    token = request.cookies.get("agentbench_session", "")
    with engine.connect() as c:
        user = (
            c.execute(
                select(users.c.id, users.c.name, users.c.email)
                .join(sessions, sessions.c.user_id == users.c.id)
                .where(sessions.c.token == digest(token), sessions.c.expires > now())
            )
            .mappings()
            .first()
        )
    if not user:
        raise HTTPException(401, "Sign in to continue")
    return dict(user)
