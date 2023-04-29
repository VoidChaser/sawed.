from flask import Flask, render_template, redirect, request, make_response, session, abort, jsonify
from data import db_session
from data.users import User
from data.files import File
from data.posts import Post
from data import db_session, news_api
from werkzeug.utils import secure_filename
from PIL import Image
# from data.post_resources import PostsResource, PostsListResource
from flask_restful import reqparse, abort, Api, Resource
import os
from forms.Register import RegisterForm
from forms.PostsForm import PostsForm
from forms.Login_form import LoginForm
from flask_login import login_user, login_required, logout_user, current_user

from flask_login import LoginManager

from static.admin_info import main_admin_log, main_admin_pass
import datetime

# Тут мы имеем импорты библиотек. Так как проект написан на фласке и его компанентах, то тут понятно,
# что используются - сам фласк и модули f-wtf, f-login, f-restful,
# также компоненты sqlalchemy и самописные модули для поддержания работы приложения


app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'base64willbeherebutnottoday.'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=31
)
# Создаём фласк-приложение, и отладной интерфейс - апи,
# для взаимодействия с программо по архитектуре rest, задаём срок жизни сессии в 31 день.


login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/sawedbase.db")
    create_admin_user('trofi', 'Kukush', main_admin_log, main_admin_pass)
    # api.add_resource(PostsListResource, '/api/v2/posts')

    # api.add_resource(PostsResource, '/api/v2/posts/<int:post_id>')
    app.run(port=8080, host='127.0.0.1')

    # с помощью написанного модуля db_session инициализируем базу данных(Если она есть, то подключаемся, если её нет,
    # то создаём заново, и подключаемся соответственно).


@app.route('/')
def index():
    session = db_session.create_session()
    posts = session.query(Post)
    if current_user.is_authenticated:
        posts = session.query(Post).filter(
            (Post.user == current_user) | (Post.is_private != True))
    else:
        posts = session.query(Post).filter(Post.is_private != True)
    images = []
    for curdir, folders, files in os.walk('static/img'):
        for file in files:
            images.append(file)
    images.sort()
    return render_template('index.html', posts=posts)


# Обработчик основной страницы на фласк. Инициализируем сессию, в базе данных ищем посты.
# Если пользователь авторизован, то показыает его посты, а также все посты в базе, а если имеем дело с анонимным
# пользователем, то показываем те, которые не приватны.


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# Обработчик для Flask-login, чтобы вытягивать конкретого пользователя при логине.


@app.route("/session_test")
def session_test():
    visits_count = session.get('visits_count', 0)
    session['visits_count'] = visits_count + 1
    return make_response(
        f"Вы пришли на эту страницу {visits_count + 1} раз")


# Сервисный обработчик для тестирования куков.

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            nickname=form.nickname.data,
            email=form.email.data,

        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


# Обработчик формы регистрации на Flask-login, где на гет запросе мы выдаём форму регистрации
# и приравниваем значения из её полей к тем,
# которые нужно заполнить. А на пост запросе вытаскиваем из формы значения, создаём пользователя.


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


# Обработчик формы авторизации, при котором мы ловим ошибки при авторизации, а если таковых нет
# - авторизируем пользователя и возвращаем исходную страницу переадрессацией.

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Обработчик для выхода из профиля.

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# Обработчик ошибки при ненахождении ресурса в базе данных или на сервере по архитектуре REST

@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


# Обработчик ошибки при невыполнени запроса, при попытке обращения к ресурсу, по архитектуре REST.

@app.route('/post', methods=['GET', 'POST'])
@login_required
def add_news():
    form = PostsForm()

    if form.validate_on_submit():
        post = Post()
        post.title = form.title.data
        post.text = form.text.data

        files_filenames = []
        db_sess = db_session.create_session()

        for file in form.files.data:
            file_name = secure_filename(file.filename)
            files_filenames.append(file_name)
            path = 'static/img/' + file_name
            file.save(path)

            nf = File()
            nf.file_link = path
            nf.file_name = file_name
            nf.user_id = current_user.id
            db_sess.add(nf)

        if files_filenames:
            post.files_linked = ', '.join(files_filenames)
            post.files_count = len(files_filenames)
            print(post.files_linked)

        post.created_date = datetime.datetime.now()
        post.is_private = form.is_private.data

        current_user.posts.append(post)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('post.html', title='Добавление новости',
                           form=form)


# Главная форма в проекте - форма публикации. Главный смысл в загрузке файлов - фотографий.
# Для каждого поста создаётся свой инструмент просмотра с помощью элементов Bootstrap
# - Карусели, и реализует функционал, с помощью которого можно просматривать фотографии.
# После подтверждения заполнения формы - отправляется пост запрос,
# после которого пост и файлы отправляются в базу данных.

@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = PostsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        post = db_sess.query(Post).filter(Post.id == id,
                                          Post.post_creator_id == current_user.id
                                          ).first()
        if post:
            form.title.data = post.title
            form.text.data = post.text
            form.is_private.data = post.is_private

        else:
            abort(404)

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        post = db_sess.query(Post).filter(Post.id == id,
                                          Post.post_creator_id == current_user.id
                                          ).first()
        if post:
            post.title = form.title.data
            post.text = form.text.data
            post.is_private = form.is_private.data
            print(form.files.data)
            if form.files.data:
                files_filenames = []

                for file in form.files.data:
                    file_name = secure_filename(file.filename)
                    files_filenames.append(file_name)
                    path = 'static/img/' + file_name
                    file.save(path)

                    nf = File()
                    nf.file_link = path
                    nf.file_name = file_name
                    nf.user_id = current_user.id
                    db_sess.add(nf)

                if files_filenames:
                    post.files_linked = ', '.join(files_filenames)
                    post.files_count = len(files_filenames)
                    print(post.files_linked)
            db_sess.commit()

            return redirect('/')
        else:
            abort(404)
    return render_template('post.html',
                           title='Редактирование новости',
                           form=form
                           )

# Обработчик формы изменения записи с учётом авторизации пользователя.


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == id,
                                      Post.post_creator_id == current_user.id
                                      ).first()
    if post:
        db_sess.delete(post)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


def create_admin_user(name, pas, ma_log, ma_pass):
    if ma_log == main_admin_log and ma_pass == main_admin_pass:
        db_ses = db_session.create_session()
        # print
        if not db_ses.query(User).filter(User.nickname == name,
                                         User.email == 'troxa75@yandex.ru',
                                         User.admin_rules == 1).all():
            user = User()
            user.nickname = name
            user.set_password(pas)
            user.email = 'troxa75@yandex.ru'
            user.modified_date = datetime.datetime.now()
            user.admin_rules = True

            db_ses.add(user)
            db_ses.commit()
            print(f"New admin called {name} was created.")

# Обработчик удаления записи.


if __name__ == '__main__':
    main()
