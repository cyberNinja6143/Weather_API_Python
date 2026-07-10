"""User table — stores login credentials with a bcrypt password hash."""

from sqlalchemy import Column, Integer, String

from models.db_models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(128), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
