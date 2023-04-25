from flask import Flask, render_template, redirect, request, make_response, session
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
from static.img_tools import create_miniature
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
    create_meet_img('static/welcome.jpg')
    meet_post()
    # add_colounists(db_session)
    # add_deploying_job(db_session)
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
    files = session.query(File)
    return render_template('index.html', posts=posts, files=files)


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
        db_sess = db_session.create_session()
        post = Post()
        post.title = form.title.data
        post.text = form.text.data

        files_filenames = []
        for file in form.files.data:
            file_name = secure_filename(file.filename)
            files_filenames.append(file_name)
            path = 'static/' + str(current_user.id) + '_' + post.title + '_' + post.text[:10] + '_' + file_name
            file.save(path)

            nf = File()
            nf.file_link = path
            nf.file_name = file_name
            nf.user_id = current_user.id
            db_sess.add(nf)

        if files_filenames:

            post.files_linked = ', '.join(list(map(lambda x: db_sess.query(File).filter(File.file_name == x).first().file_link, files_filenames)))
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



def create_meet_img(path):


    db_ses = db_session.create_session()

    file = File()
    file.user_id = db_ses.query(User).filter(User.admin_rules == 1).first().id
    file.file_link = path
    # file.file_mini_link = create_miniature(path)
    # print(file.file_link, file.file_mini_link)
    # print(path)

    db_ses.add(file)
    db_ses.commit()


def meet_post():
    db_ses = db_session.create_session()

    post = Post()
    post.post_creator_id = db_ses.query(User).filter(User.admin_rules == 1).first().id
    admin_id = post.post_creator_id
    post.title = 'Приветствую'
    post.text = 'Это сообщение было создано автоматически.'
    post.created_date = datetime.datetime.now()
    print(list(map(lambda x: x.user.id, db_ses.query(File).all())))
    print(post.post_creator_id)
    quer = db_ses.query(File).filter(File.user_id == post.post_creator_id).first()
    post.files_linked = ', '.join([quer.file_link])
    post.files_count = 1


    # post.file_link = db_ses.query(File).filter(File.user_id == post.post_creator_id).first()
    print(post.files_linked)
    db_ses.add(post)
    db_ses.commit()






# def meet_post(db_ses):
#     file = File()
#     file.


# def add_deploying_job(db_ses):
#     job = Jobs()
#     job.team_leader = 1
#     job.job = 'deployment of residential modules 1 and 2'
#     job.work_size = 15
#     job.collaborators = '2, 3'
#     job.start_date = datetime.datetime.now()
#     job.is_finished = False
#
#     db_sess = db_ses.create_session()
#     db_sess.add(job)
#     db_sess.commit()
#
#
# def add_colounists(db_ses):
#     user = User()
#     user.surname = 'Scott'
#     user.name = 'Ridley'
#     user.age = 21
#     user.position = 'captain'
#     user.speciality = 'research engineer'
#     user.address = 'module_1'
#     user.email = "scott_chief@mars.org"
#
#     user1 = User()
#     user1.surname = 'Mickey'
#     user1.name = 'Mouse'
#     user1.age = 22
#     user1.position = 'employer'
#     user1.speciality = 'cleaner'
#     user1.address = 'module_2'
#     user1.email = "mickey@mars.org"
#
#     user2 = User()
#     user2.surname = 'Onion'
#     user2.name = 'Skycryer'
#     user2.age = 19
#     user2.position = 'junior spec.'
#     user2.speciality = 'pilot'
#     user2.address = 'module_3'
#     user2.email = "onion_skycryer@mars.org"
#
#     db_sess = db_ses.create_session()
#     db_sess.add(user)
#     db_sess.add(user1)
#     db_sess.add(user2)
#
#     db_sess.commit()




if __name__ == '__main__':
    main()

