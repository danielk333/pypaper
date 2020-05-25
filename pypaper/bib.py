import bibtexparser
from bibtexparser.bparser import BibTexParser

from . import config

def load_bibtex(path):
    parser = BibTexParser()
    parser.ignore_nonstandard_types = False
    parser.homogenise_fields = False

    if path.stat().st_size == 0:
        return bibtexparser.bibdatabase.BibDatabase()

    with open(path, 'r') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser)
    return bib_database


def _format_author(auth):
    auth = auth.replace('{','')
    auth = auth.replace('}','')
    auth = auth.split(',')
    auth_ = []
    for a in auth:
        auth_ += a.split('and')
    return auth_[0]


def rename_bibtex(bib_database):
    tlen_ = int(config.config['General']['title include'])
    for entry in bib_database.entries:

        title_str = entry['title'].replace('{','')
        title_str = title_str.replace('}','').strip()
        title_str = title_str.replace(' ','')
        if len(title_str) > tlen_:
            title_str = title_str[:tlen_]

        new_id = _format_author(entry['author'])\
                    + str(entry['year'])\
                    + title_str
        new_id = ''.join(e for e in new_id if e.isalnum())

        entry['ID'] = new_id


def save_bibtex(path, bib_database):
    with open(path, 'w+') as bibtex_file:
        bibtexparser.dump(bib_database, bibtex_file)