from . import db_session
from .posts import Post
from flask import abort, jsonify
from flask_restful import Resource
import flask_reqparse

parser = flask_reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)
parser.add_argument('is_private', required=True, type=bool)
parser.add_argument('is_published', required=True, type=bool)
parser.add_argument('user_id', required=True, type=int)

def abort_if_news_not_found(post_id):
    session = db_session.create_session()
    posts = session.query(Post).get(post_id)
    if not posts:
        abort(404, message=f"Post {post_id} not found")


class PostsResource(Resource):
    def get(self, posts_id):
        abort_if_news_not_found(posts_id)
        session = db_session.create_session()
        posts = session.query(Post).get(posts_id)
        return jsonify({'posts': posts.to_dict(
            only=('title', 'text', 'post_creator_id', 'is_private'))})

    def delete(self, posts_id):
        abort_if_news_not_found(posts_id)
        session = db_session.create_session()
        posts = session.query(Post).get(posts_id)
        session.delete(posts)
        session.commit()
        return jsonify({'success': 'OK'})

class PostsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        posts = session.query(Post).all()
        return jsonify({'posts': [item.to_dict(
            only=('title', 'text', 'post_creator_id')) for item in posts]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        posts = Post(
            title=args['title'],
            text=args['text'],
            post_creator_id=args['post_creator_id'],
            is_published=args['is_published'],
            is_private=args['is_private']
        )
        session.add(posts)
        session.commit()
        return jsonify({'success': 'OK'})