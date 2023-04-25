import datetime

import sqlalchemy
from sqlalchemy import orm

from . db_session import SqlAlchemyBase


class File(SqlAlchemyBase):
    posts = orm.relationship("Post", back_populates='file')
    __tablename__ = 'files'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    file_name = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    file_link = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    file_mini_link = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    creation_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now(), nullable=True)
    user = orm.relationship("User")

