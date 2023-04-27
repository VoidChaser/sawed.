import flask
from flask import jsonify, request
from flask_login import current_user

from . import db_session
from .posts import Post

blueprint = flask.Blueprint(
    'post_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/posts', methods=['GET'])
def get_posts():
    db_sess = db_session.create_session()
    news = db_sess.query(Post).all()
    return jsonify(
        {
            'news':
                [item.to_dict(only=('title', 'text', 'post_creator_id'))
                 for item in news]
        }
    )

@blueprint.route('/api/posts/<int:post_id>', methods=['GET'])
def get_one_news(post_id):
    db_sess = db_session.create_session()
    posts = db_sess.query(Post).get(post_id)
    if not posts:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'posts': posts.to_dict(only=(
                'title', 'text', 'post_creator_id', 'is_private'))
        }
    )

@blueprint.route('/api/posts', methods=['POST'])
def create_post():
    if not request.json:
        return jsonify({'error': 'Empty request'})
    elif not all(key in request.json for key in
                 ['title', 'text', 'post_creator_id', 'is_private']):
        return jsonify({'error': 'Bad request'})
    if request.json['post_creator_id'] == current_user.id:
        db_sess = db_session.create_session()
        post = Post(
            title=request.json['title'],
            text=request.json['text'],
            post_creator_id=request.json['post_creator_id'],
            is_private=request.json['is_private']
        )
        db_sess.add(post)
        db_sess.commit()
        return jsonify({'success': 'OK'})
    else:
        return jsonify({'error': 'permission denied'})


@blueprint.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_news(post_id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).get(post_id)
    if post.post_creator_id == current_user.id:
        if not post:
            return jsonify({'error': 'Not found'})
        db_sess.delete(post)
        db_sess.commit()
        return jsonify({'success': 'OK'})
    else:
        return jsonify({'error': 'Permission denied'})
