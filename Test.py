from flask import Flask, request, render_template_string

import os
from PyPDF2 import PdfReader
import sqlite3
from striprtf.striprtf import rtf_to_text
import pypandoc

app = Flask(__name__)

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))


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


@app.route('/<id>')
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
