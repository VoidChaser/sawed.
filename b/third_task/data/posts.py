import datetime

import sqlalchemy
from sqlalchemy import orm

from . db_session import SqlAlchemyBase


class Post(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    post_creator_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    title = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    text = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    files_linked = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('files.file_link'), nullable=True)
    files_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now(), nullable=True)

    user = orm.relationship("User")
    file = orm.relationship("File")


