from ..extensions import db
from ..models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        if not user_id:
            return None
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def create_user(username, email, password_hash):
        user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        return user
