from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
import codecs
import pathlib
import string

path = pathlib.Path('10.1.1.453.9156.pdf')

fd = open(path, 'rb')

parser = PDFParser(fd)
pdf = PDFDocument(parser)

print(pdf)
print(pdf.info)


class MyTextConverter(TextConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_output = []

    def write_text(self, text):
        self.text_output.append(text)


if len(pdf.info) > 0:
    for field in pdf.info[0].keys():
        raw = pdf.info[0][field]
        value = None
        if isinstance(raw, bytes):
            encoding = None

            if raw.startswith(codecs.BOM_UTF8):
                encoding = 'utf-8'
            elif raw.startswith(codecs.BOM_UTF16_BE):
                encoding = 'utf-16-be'
            elif raw.startswith(codecs.BOM_UTF16_LE):
                encoding = 'utf-16-le'
            elif raw.startswith(codecs.BOM_UTF32_BE):
                encoding = 'utf-32-be'
            elif raw.startswith(codecs.BOM_UTF32_LE):
                encoding = 'utf-32-le'

            if encoding is not None:
                try:
                    value = str(raw, encoding=encoding).strip()
                    value = value[1:]  # drop the BOM
                except UnicodeError:
                    continue
        elif isinstance(raw, str) and len(raw.strip()) > 0:
            value = raw.strip()
        else:
            continue

        print(f'{field}: {value}')


laparams = LAParams()
laparams.all_texts = True
laparams.detect_vertical = True
rmngr = PDFResourceManager(caching=True)
device = MyTextConverter(rmngr, None, laparams=laparams, imagewriter=None)
interpreter = PDFPageInterpreter(rmngr, device)
for page in PDFPage.get_pages(fd, set(), check_extractable=True):
    interpreter.process_page(page)
fulltext = (''.join(device.text_output)).strip()
fd.close()
some_data = len(fulltext) > 0
lines = fulltext.split("\n")
title = string.capwords(lines[0])

print(lines[0:10])
print(title)


import bibtexparser
from bibtexparser.bparser import BibTexParser

parser = BibTexParser()
parser.ignore_nonstandard_types = False
parser.homogenise_fields = False

with open('bibtex.bib') as bibtex_file:
    bib_database = bibtexparser.load(bibtex_file, parser)

print(bib_database.entries)