import sqlite3
from striprtf.striprtf import rtf_to_text
import pypandoc

with open("books/19. The Horror of the Heights Author Arthur Conan Doyle.rtf", "r") as f:
    red = f.readlines()
    spisok = [elem.replace("\n", "") for elem in "".join(red).split(". \n")]
    print(len(spisok))

# . \n
# . \n
