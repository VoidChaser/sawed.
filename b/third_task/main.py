from flask import Flask, render_template, redirect, request, make_response, session, abort
from data import db_session
from data.users import User
from data.files import File
from data.posts import Post
from werkzeug.utils import secure_filename
from PIL import Image
import os
from forms.Register import RegisterForm
from forms.PostsForm import PostsForm
from forms.Login_form import LoginForm
from flask_login import login_user, login_required, logout_user, current_user

from flask_login import LoginManager

from static.admin_info import main_admin_log, main_admin_pass
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'base64willbeherebutnottoday.'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=31
)

login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/sawedbase.db")
    create_admin_user('trofi', 'Kukush', main_admin_log, main_admin_pass)
    # create_meet_img('static/img/welcome.jpg')
    # meet_post()
    app.run()


@app.route('/')
def index():
    session = db_session.create_session()
    posts = session.query(Post)
    if current_user.is_authenticated:
        posts = session.query(Post).filter(
            (Post.user == current_user) | (Post.is_private != True))
    else:
        posts = session.query(Post).filter(Post.is_private != True)
    # files = session.query(File)
    images = []
    for curdir, folders, files in os.walk('static/img'):
        for file in files:
            images.append(file)
    images.sort()
    return render_template('index.html', posts=posts)
    # return render_template('index.html', posts=posts, files=files)




@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/session_test")
def session_test():
    visits_count = session.get('visits_count', 0)
    session['visits_count'] = visits_count + 1
    return make_response(
        f"Вы пришли на эту страницу {visits_count + 1} раз")

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/post',  methods=['GET', 'POST'])
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






if __name__ == '__main__':
    main()

