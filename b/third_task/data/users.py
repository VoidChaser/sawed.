import datetime
import sqlalchemy
from sqlalchemy import orm
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

from . db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    files = orm.relationship("File", back_populates='user')
    posts = orm.relationship("Post", back_populates='user')
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    nickname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())
    admin_rules = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

