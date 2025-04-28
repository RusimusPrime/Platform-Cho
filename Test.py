from flask import Flask, request, render_template_string, redirect
import os
from PyPDF2 import PdfReader

app = Flask(__name__)

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))


@app.route("/", methods=["GET", "POST"])
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


def action(name):
    reader = PdfReader(name)
    page = reader.pages
    with open("book.rtf", 'w') as file:
        for elem in page:
            file.write(elem.extract_text())


if __name__ == "__main__":
    app.run(debug=True)
