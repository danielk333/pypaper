import pathlib

import bibtexparser
from bibtexparser.bparser import BibTexParser
import inquirer

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


def _clean_id(field):
    return str(field).replace(' ', '_').strip()


def rename_bibtex(bib_database):
    tlen_ = int(config.config['General']['title include'])
    for entry in bib_database.entries:

        if 'title' not in entry:
            print(config.Terminal.RED + 'bibtex entry title missing' + config.Terminal.END)
            for key in entry:
                print(f'- {config.Terminal.BOLD + key + config.Terminal.END}: {entry[key]}')
            questions = [
                inquirer.Text('title', message="Enter title (leave blank to skip)"),
            ]
            answers = inquirer.prompt(questions)
            if len(answers['title']) > 0:
                entry['title'] = answers['title']
            else:
                print('Skipping entry')
                continue

        title_str = str(entry['title'])
        title_str = title_str.replace('{','').replace('}','').strip()
        title_str = title_str.replace(' ','_')
        if tlen_ > 0:
            if len(title_str) > tlen_:
                title_str = title_str[:tlen_]

        if 'year' in entry:
            year_str = str(entry['year'])
        else:
            year_str = 'yyyy'

        if 'author' in entry:
            author_str = _format_author(str(entry['author']))
        elif 'institution' in entry:
            author_str = _clean_id(entry['institution'])
        elif 'publisher' in entry:
            author_str = _clean_id(entry['publisher'])
        elif 'editor' in entry:
            author_str = _clean_id(entry['editor'])
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