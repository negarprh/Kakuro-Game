"""
Authentication service for Iteration 1.
Supports flows: Sign Up and Log In.
"""

from __future__ import annotations

from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from ..models import user as user_repo


MIN_PASSWORD_LENGTH = 6


def _email_looks_valid(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1]


def submit_signup(
    db_path: Path,
    username: str,
    email: str,
    password: str,
) -> tuple[bool, str]:
    # Diagram mapping: submitSignUp(username, email, password).
    username = (username or "").strip()
    email = (email or "").strip().lower()
    password = password or ""

    if not username or not email or not password:
        return False, "All fields are required."

    if not _email_looks_valid(email):
        return False, "Please provide a valid email address."

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."

    # Precondition: username must be unique in DB.
    if user_repo.get_user_by_username(username, db_path):
        return False, "Username already exists."

    # Precondition: email must be unique in DB.
    if user_repo.get_user_by_email(email, db_path):
        return False, "Email already exists."

    # Postcondition: create and persist user with hashed password.
    password_hash = generate_password_hash(password)
    user_repo.create_user(username, email, password_hash, db_path)
    return True, "Account created successfully. Please log in."


def submit_login(db_path: Path, email: str, password: str):
    # Diagram mapping: submitLogin(email, password).
    email = (email or "").strip().lower()
    password = password or ""

    if not email or not password:
        return None

    user = user_repo.get_user_by_email(email, db_path)
    if user is None:
        return None

    # Precondition: provided password matches stored password hash.
    if not check_password_hash(user.passwordHash, password):
        return None

    # Postcondition: authenticated user is returned to route for session creation.
    return user
