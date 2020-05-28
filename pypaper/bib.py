import pathlib

import bibtexparser
from bibtexparser.bparser import BibTexParser

from . import config

def get_parser():
    parser = BibTexParser(common_strings=True, interpolate_strings=False)
    parser.ignore_nonstandard_types = False
    parser.homogenise_fields = False
    return parser


def load_bibtex(paths):

    parser = get_parser()

    if isinstance(paths, pathlib.Path):
        paths = [paths]

    st_size = 0
    for path in paths:
        st_size += path.stat().st_size
    if st_size == 0:
        return bibtexparser.bibdatabase.BibDatabase()

    bib_data = ''
    for path in paths:
        with open(path, 'r') as bibtex_file:
            bib_data += bibtex_file.read()

    bib_database = bibtexparser.loads(bib_data, parser)
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
        title_str = title_str.replace(' ','_')
        if tlen_ > 0:
            if len(title_str) > tlen_:
                title_str = title_str[:tlen_]

        if 'year' in entry:
            year_str = str(entry['year'])
        else:
            year_str = 'yyyy'

        if 'author' in entry:
            author_str = _format_author(entry['author'])
        elif 'institution' in entry:
            author_str = entry['institution'].replace(' ', '_').strip()
        elif 'publisher' in entry:
            author_str = entry['publisher'].replace(' ', '_').strip()
        else:
            author_str = 'unknown'

        new_id = author_str\
                    + year_str\
                    + title_str
        new_id = ''.join(e for e in new_id if e.isalnum() or e == '_')

        entry['ID'] = new_id


def save_bibtex(path, bib_database):
    with open(path, 'w+') as bibtex_file:
        bibtexparser.dump(bib_database, bibtex_file)