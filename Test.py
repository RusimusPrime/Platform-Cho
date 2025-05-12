from flask import Flask, request, render_template_string, render_template, redirect
import hashlib
import os
from PyPDF2 import PdfReader
import sqlite3
from striprtf.striprtf import rtf_to_text

app = Flask(__name__)

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))
AUTHORIZED = False


@app.route("/load", methods=["GET", "POST"])
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
        action(file.filename)
        os.remove(save_path)
        return f"Файл {file.filename} успешно сохранён в папку приложения"

    return render_template_string("""
        <html>
            <body>
                <form method="POST" enctype="multipart/form-data">
                    <input type="file" name="pdf_file" accept="application/pdf" required>
                    <button type="submit">Загрузить PDF</button>
                </form>
            </body>
        </html>
    """)


@app.route('/watch/<id>')
def show_file(id):
    connection = sqlite3.connect('cho.db')
    cur = connection.cursor()
    result = cur.execute("""SELECT path FROM bible WHERE id = ?""", (id,)).fetchall()[0][0]
    with open(result, 'r') as f:
        rtf_content = f.read()
    text = rtf_to_text(rtf_content)

    html_text = text.replace('\n\n', '</p><p>').replace('\n', '<br>')
    html_text = f'<p>{html_text}</p>'

    return render_template_string(html_text)


@app.route('/books')
def books():
    con = sqlite3.connect("cho.db")
    cur = con.cursor()
    result = cur.execute("""SELECT id, name FROM bible""").fetchall()
    print(result)
    return result


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        connection = sqlite3.connect('cho.db')
        cur = connection.cursor()
        result = cur.execute("""SELECT * FROM users""").fetchall()
        cur.execute('INSERT INTO users (id, login, password) VALUES (?, ?, ?)',
                    (len(result) + 1, request.form.get('userName'),
                     hashlib.sha256(request.form.get('password').encode()).hexdigest(),))
        connection.commit()
        connection.close()
        return redirect("/home", code=302)
    return render_template('register_window.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/singing', methods=['GET', 'POST'])
def singing():
    global AUTHORIZED
    if request.method == 'POST':
        try:
            connection = sqlite3.connect('cho.db')
            cur = connection.cursor()
            result = cur.execute("""SELECT login FROM users where password = ?""",
                                 (hashlib.sha256(request.form.get('password').encode()).hexdigest(),)).fetchall()[0][0]
            print(result)
            connection.close()
        except TypeError:
            return "Ничего не нашлось"
        except IndexError:
            return "Ничего не нашлось"
        else:
            if result == request.form.get('userName'):
                AUTHORIZED = True
                return redirect("/home", code=302)
            else:
                return "неправиьный логин"
    return render_template('singing in account.html')


def action(name):
    reader = PdfReader(name)
    page = reader.pages
    with open(f"books/{name[:name.find(".pdf")] + ".rtf"}", 'w') as file:
        file.write("\n".join(
            ["\t" + elem.replace("\n", "") for elem in "".join([elem.extract_text() for elem in page]).split(". \n")]))

    connection = sqlite3.connect('cho.db')
    cur = connection.cursor()
    result = cur.execute("""SELECT * FROM bible""").fetchall()
    cur.execute('INSERT INTO bible (id, name, path) VALUES (?, ?, ?)',
                (len(result) + 1, name[:name.find(".pdf")] + ".rtf", f"books/{name[:name.find(".pdf")] + ".rtf"}",))
    connection.commit()
    connection.close()


if __name__ == "__main__":
    app.run(debug=True)
