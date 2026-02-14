from werkzeug.security import check_password_hash, generate_password_hash

from ..repositories.user_repository import UserRepository


MIN_PASSWORD_LENGTH = 6


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def validate_signup_data(username, email, password):
    errors = []

    if not username or len(username.strip()) < 3:
        errors.append("Username must be at least 3 characters.")

    if not email or "@" not in email or "." not in email.split("@")[-1]:
        errors.append("Email address is invalid.")

    if not password or len(password) < MIN_PASSWORD_LENGTH:
        errors.append(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )

    return errors


def register_user(username, email, password):
    username = username.strip()
    email = email.strip().lower()

    errors = validate_signup_data(username, email, password)
    if errors:
        raise ValueError(" ".join(errors))

    if UserRepository.get_by_username(username):
        raise ValueError("Username already exists.")

    if UserRepository.get_by_email(email):
        raise ValueError("Email already exists.")

    password_hash = hash_password(password)
    return UserRepository.create_user(username, email, password_hash)


def authenticate_user(identifier, password):
    identifier = (identifier or "").strip()
    password = password or ""
    if not identifier or not password:
        return None

    user = UserRepository.get_by_username(identifier)
    if user is None and "@" in identifier:
        user = UserRepository.get_by_email(identifier.lower())

    if user and verify_password(user.password_hash, password):
        return user

    return None
