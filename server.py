from flask import Flask, request, render_template_string, render_template, redirect, url_for
import hashlib
import os
from PyPDF2 import PdfReader
from flask_login import login_required
from striprtf.striprtf import rtf_to_text
from flask_sqlalchemy import SQLAlchemy
from flask_login import logout_user, LoginManager
from flask_login import login_user
from flask_login import UserMixin
from datetime import datetime
from flask_login import current_user

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cho.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a9f8s7d6f5g4h3j2k1l0qwertyuiop'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'singing'

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))


class Bible(db.Model):
    __tablename__ = 'bible'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    path = db.Column(db.String, nullable=False)
    id_user = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route("/load", methods=["GET", "POST"])
@login_required
def upload_pdf():
    if request.method == "POST":
        if "pdf_file" not in request.files:
            return "Файл не найден в запросе", 400

        file = request.files["pdf_file"]

        if file.filename == "":
            return "Файл не выбран", 400
        if not file.filename.lower().endswith(".pdf"):
            return "Можно загружать только PDF файлы", 400

        save_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(save_path)

        new_book = Bible(
            name=file.filename,
            path=save_path,
            id_user=current_user.id,
            date=datetime.utcnow()
        )
        db.session.add(new_book)
        db.session.commit()
        print(current_user.id)
        action(file.filename)

        os.remove(save_path)
        return redirect("/home", code=302)

    return render_template("download.html")


@app.route('/watch/<int:id>')
@login_required
def show_file(id):
    bible_entry = Bible.query.get(id)
    if not bible_entry:
        return "Запись не найдена", 404
    with open(bible_entry.path, 'r', encoding='utf-8') as f:
        rtf_content = f.read()
    text = rtf_to_text(rtf_content)

    html_text = text.replace('\n\n', '</p><p>').replace('\n', '<br>')
    html_text = f'<p>{html_text}</p>'

    return render_template_string(html_text)


@app.route('/books')
@login_required
def books():
    result = Bible.query.with_entities(Bible.id, Bible.name).all()
    return {id: name for id, name in result}


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if not request.form.get('userName') or not request.form.get('password'):
            return "Заполните все поля", 400

        existing_user = Users.query.filter_by(login=request.form.get('userName')).first()
        if existing_user:
            return "Пользователь с таким логином уже существует", 400

        hashed_password = hashlib.sha256(request.form.get('password').encode()).hexdigest()
        max_id = db.session.query(db.func.max(Users.id)).scalar() or 0
        new_user = Users(id=max_id + 1, login=request.form.get('userName'), password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/home", code=302)
    return render_template('register_window.html')


@app.route('/home')
def home():
    return render_template('index.html')


@app.route('/rec')
@login_required
def rec():
    return render_template('recomindation.html')


@app.route('/')
def base():
    return redirect("/home", code=302)


@app.route('/singing', methods=['GET', 'POST'])
def singing():
    if request.method == 'POST':
        if not request.form.get('userName') or not request.form.get('password'):
            return "Заполните все поля", 400

        hashed_password = hashlib.sha256(request.form.get('password').encode()).hexdigest()
        user = Users.query.filter_by(login=request.form.get('userName'), password=hashed_password).first()
        if user:
            login_user(user)
            return redirect(url_for('home'))
        else:
            return "Неверный логин или пароль", 401
    return render_template('singing in account.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


def action(name):
    reader = PdfReader(name)
    pages = reader.pages
    text_content = "".join([page.extract_text() for page in pages if page.extract_text()])

    rtf_text = "\n".join(
        ["\t" + elem.replace("\n", "") for elem in text_content.split(". \n")]
    )

    rtf_path = f"books/{name[:name.find('.pdf')]}.rtf"
    os.makedirs('books', exist_ok=True)
    with open(rtf_path, 'w', encoding='utf-8') as file:
        file.write(rtf_text)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
