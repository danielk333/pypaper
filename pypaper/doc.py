from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
import codecs
from io import StringIO

class MyTextConverter(TextConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_output = []

    def write_text(self, text):
        self.text_output.append(text)


def parse_pdf(path):

    fd = open(path, 'rb')
    retstr = StringIO()
    
    laparams = LAParams()
    laparams.all_texts = True
    laparams.detect_vertical = True
    rmngr = PDFResourceManager(caching=True)
    device = MyTextConverter(rmngr, retstr, laparams=laparams, imagewriter=None)
    interpreter = PDFPageInterpreter(rmngr, device)
    for page in PDFPage.get_pages(fd, set(), check_extractable=True):
        interpreter.process_page(page)
    fulltext = (''.join(device.text_output)).strip()
    fd.close()
    if len(fulltext) == 0:
        return []
    lines = fulltext.split("\n")

    return lines