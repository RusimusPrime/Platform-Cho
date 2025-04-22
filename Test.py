from PyPDF2 import PdfReader

reader = PdfReader("19. The Horror of the Heights Author Arthur Conan Doyle.pdf")
page = reader.pages
with open("book.rtf",  'w') as file:
    for elem in page:
        file.write(elem.extract_text())