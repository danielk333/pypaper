
#Python standard
from cmd import Cmd
from glob import glob
import os
import pathlib
import subprocess
import re
import string

#Third party
import bibtexparser
import inquirer

#Local
from . import config
from . import bib

try:
    from . import doc
except ImportError:
    doc = None

try:
    from . import ads
except Exception:
    ads = None


def doc_index_arg_check(func):
    def checked_func(self, args):
        if self.new_links is None:
            print('Nothing has been picked up')
            return
        if len(self.new_links) == 0:
            print('Nothing has been picked up')
            return

        if len(args) == 0:
            opts_ = [file.name for file in self.new_links]

            questions = [
                inquirer.List('doc',
                    message='Which picked up document?',
                    choices=opts_ + ['NONE'],
                    carousel=True,
                ),
            ]
            answers = inquirer.prompt(questions)
            answer = answers['doc']
            if answer == 'NONE':
                print('No document chosen')
                return
            else:
                args = str(opts_.index(answer))

        elif not args.strip().isnumeric():
            print('No valid document index given')
            return

        return func(self, args)
    checked_func.__doc__ = func.__doc__
    return checked_func



def bib_index_arg_check(func):
    def checked_func(self, args):
        if self.bibtex is None:
            print('No bibtex loaded')
            return
        if len(self.bibtex.entries) == 0:
            print('No bibtex entries loaded')
            return

        if len(args) == 0:
            opts_ = self._list_bib()

            questions = [
                inquirer.List('bib',
                    message='Which bibtex entry?',
                    choices=opts_ + ['NONE'],
                    carousel=True,
                ),
            ]
            answers = inquirer.prompt(questions)
            answer = answers['bib']
            if answer == 'NONE':
                print('No bibtex entry chosen')
                return
            else:
                args = str(opts_.index(answer))

        elif not args.strip().isnumeric():
            print('No valid document index given')
            return

        return func(self, args)
    checked_func.__doc__ = func.__doc__
    return checked_func


def open_viewer(path):
    subprocess.run(
        [config.config['General']['viewer'], str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class Shell(Cmd):

    def do_docpickup(self, args):
        '''pdf files to add to database'''
        docs = glob(str(config.PICKUP_FOLDER / '*.pdf'))
        docs = [pathlib.Path(p) for p in docs]

        self.new_links = docs


    def do_pickup(self, args):
        '''Pickup bibtex files and pdf files to add to database'''

        self.do_docpickup('')

        bibs = glob(str(config.PICKUP_FOLDER / '*.bib'))
        bibs = [pathlib.Path(p) for p in bibs]

        for b_path in bibs:
            print('Picking up from "{}"'.format(b_path))
        if len(bibs) > 0:
            b = bib.load_bibtex(bibs)
            _skip = 0
            _add = 0        
            bib.rename_bibtex(b)
            #add non-duplicates
            for in_entry in b.entries:
                _exists = False
                if 'title' not in in_entry:
                    continue

                for entry in self.bibtex.entries:
                    if in_entry['ID'] == entry['ID']:
                        _exists = True
                    if str(in_entry['title']) == str(entry['title']):
                        _exists = True

                if not _exists:
                    self.bibtex.entries.append(in_entry)
                    _add += 1
                else:
                    _skip += 1
            if _skip > 0:
                print('Skipped {} duplicates'.format(_skip))

            _add_str = 0
            for key in b.strings:
                if key not in self.bibtex.strings:
                    self.bibtex.strings[key] = b.strings[key]
                    _add_str += 1

            print('Added {} entries'.format(_add))
            print('Added {}/{} strings'.format(_add_str, len(b.strings) - len(bibtexparser.bibdatabase.COMMON_STRINGS)))
            for b_path in bibs:
                os.rename(b_path, config.TRASH_FOLDER / b_path.name)

        if len(self.new_links) == 0 and len(bibs) == 0:
            print('Pickup folder empty')
        else:
            self.do_save('')


    def do_save(self, args):
        '''Save bibtex file'''
        bib.save_bibtex(config.BIB_FILE, self.bibtex)


    @bib_index_arg_check
    def do_bibrm(self, args):
        '''Remove bibtex entry'''
        id_ = self._get_bibid(args)
        if id_ is None:
            print('Index out of range')
            return
        del self.bibtex.entries[id_]
        self.do_save('')

    @bib_index_arg_check
    def do_bibview(self, args):
        '''View bibtex entry'''
        id_ = self._get_bibid(args)
        if id_ is None:
            print('Index out of range')
            return
        entry = self.bibtex.entries[id_]
        print(config.Terminal.PURPLE + entry['ID'] +  config.Terminal.END)
        for key in entry:
            print(f'- {config.Terminal.BOLD + key + config.Terminal.END}: {entry[key]}')

    @bib_index_arg_check
    def do_id(self, args):
        '''Copy bibtex entry to clipboard'''
        id_ = self._get_bibid(args)
        if id_ is None:
            print('Index out of range')
            return
        entry = self.bibtex.entries[id_]

        data = entry['ID']
        cmd = ['xsel','-b','-i']
        subprocess.run(cmd, universal_newlines=True, input=data)
        print('Copied ID to clipboard')

    @bib_index_arg_check
    def do_clip(self, args):
        '''Copy bibtex entry to clipboard'''

        id_ = self._get_bibid(args)
        if id_ is None:
            print('Index out of range')
            return
        entry = self.bibtex.entries[id_]

        bib_database = bibtexparser.bibdatabase.BibDatabase()
        bib_database.entries = [entry]

        data = bibtexparser.dumps(bib_database)
        cmd = ['xsel','-b','-i']
        subprocess.run(cmd, universal_newlines=True, input=data)
        print('Copied bibtex entry to clipboard')


    def do_stat(self, args):
        '''Display current statistics'''
        print(f'{len(self.bibtex.entries)} bibtex entries loaded')
        print(f'{len(self.current_bibtex)} entries in current list')
        if self.new_links is not None:
            print(f'{len(self.new_links)} picked up documents to link')
        if self.docs is not None:
            print(f'{len(self.docs)} documents in database')


    def do_load(self, args):
        '''Load bibtex file and list of papers'''
        self.bibtex = bib.load_bibtex(config.BIB_FILE)

        self.bibtex.comments = []

        bib.rename_bibtex(self.bibtex)
        self.current_bibtex = []

        print('Bib load: {} entries loaded'.format(len(self.bibtex.entries)))
        self.docs = glob(str(config.PAPERS_FOLDER / '*.pdf'))
        self.docs = [pathlib.Path(p) for p in self.docs]

        print('DOCS load: {} papers found'.format(len(self.docs)))


    def do_doclist(self, args):
        '''Lists all unlinked documents in pickup'''
        if self.new_links is None:
            print('Nothing has been picked up')
            return
        for id_,file in enumerate(self.new_links):
             print(f'{id_:<4}: {file.parts[-1]}')

    @doc_index_arg_check
    def do_docviewpdf(self, args):
        '''Views an picked up document'''
        if not args.strip().isnumeric():
            print('No valid document index given')
            return

        if self.new_links is None:
            print('Nothing has been picked up')
            return

        open_viewer(self.new_links[int(args)])


    @doc_index_arg_check
    def do_docview(self, args):
        '''Views an picked up document'''

        if doc is None:
            open_viewer(self.new_links[int(args)])
        else:
            lines = doc.parse_pdf(self.new_links[int(args)])
            title = string.capwords(lines[0])
            print(title)
            print('='*len(title))
            for i in range(10):
                print(lines[i])


    @doc_index_arg_check
    def do_doctrash(self, args):
        '''Moves a document to trash folder in database'''
        os.rename(self.new_links[int(args)], config.TRASH_FOLDER / self.new_links[int(args)].name)
        del self.new_links[int(args)]


    def do_bib(self, args):
        '''Lists selected bibtex entries in database, syntax: --limit [int] [field]=[regex] &/| [field]=[regex]...'''

        if len(args) > 0:
            find_limit = args.find('--limit', 0)
            if find_limit != -1:
                find_space = args.find(' ', find_limit+8)
                if find_space == -1:
                    self.limit = int(args[(find_limit+8):])
                    find_space = len(args)
                else:
                    self.limit = int(args[(find_limit+8):find_space])

                args = args.replace(args[find_limit:find_space], '')
        args = args.strip()

        if len(args) > 0:
            arg_list = []
            operators = []
            find_ret = 0
            find_pos = 0

            while True:
                eq_pos = args.find('=', find_pos)
                if eq_pos == -1:
                    break
                key = args[find_pos:eq_pos].strip()
                if eq_pos+1 >= len(args):
                    arg_list.append([len(arg_list), key, ''])
                    break

                if args[eq_pos+1] in ['"', "'"]:
                    find_pos = args.find(args[eq_pos+1], eq_pos+2)
                    if find_pos == -1:
                        raise Exception('No closing quotation mark on pattern')
                    pattern = args[(eq_pos+2):find_pos]
                    find_pos += 1
                else:
                    find_pos = args.find(' ', eq_pos)
                    if find_pos == -1:
                        find_pos = len(args)
                    pattern = args[(eq_pos+1):find_pos]

                arg_list.append([len(arg_list), key, pattern])

                if find_pos+1 >= len(args):
                    break
                else:
                    operators.append(args[find_pos+1])
                    find_pos += 3

            self.current_bibtex = []
            for id_,entry in enumerate(self.bibtex.entries):
                add_ = None
                for arg_id, key, pattern in arg_list:
                    if key in entry:
                        resh = re.search(pattern, str(entry[key]))
                        if add_ is None:
                            add_ = resh is not None
                        else:
                            operator = operators[arg_id-1]
                            if operator == '&':
                                add_ = add_ and resh is not None
                            elif operator == '|':
                                add_ = add_ or resh is not None
                if add_ is None:
                    add_ = False
                if add_:
                    self.current_bibtex.append(id_)

            if len(self.current_bibtex) == 0:
                print('No matches')
                return

        strs_ = self._list_bib()
        for str_ in strs_:
            print(str_)


    def _list_bib(self):
        if len(self.current_bibtex) == 0:
            if len(self.bibtex.entries) > self.limit:
                display_bibtex = list(range(self.limit))
            else:
                display_bibtex = list(range(len(self.bibtex.entries)))
        else:
            if len(self.current_bibtex) > self.limit:
                display_bibtex = self.current_bibtex[:self.limit]
            else:
                display_bibtex = self.current_bibtex

        strs_ = [None]*len(display_bibtex)
        for id_, cid_ in enumerate(display_bibtex):
            entry = self.bibtex.entries[cid_]
            file_ = '   '
            for f in self.docs:
                if f.stem == entry["ID"]:
                    file_ = 'pdf'

            strs_[id_] = f'{id_:<4}[{file_}]: {entry["ID"]}'
        return strs_

    def _get_bibid(self, args):
        if len(self.current_bibtex) > 0:
            if int(args) > len(self.current_bibtex):
                id_ = None
            else:
                id_ = self.current_bibtex[int(args)]
        else:
            if int(args) > len(self.bibtex.entries):
                id_ = None
            else:
                id_ = int(args)
        return id_

    @bib_index_arg_check
    def do_open(self, args):
        '''Opens paper linked to bibtex entry'''
        id_ = self._get_bibid(args)
        if id_ is None:
            print('Index out of range')
            return

        fname = config.PAPERS_FOLDER / f'{self.bibtex.entries[id_]["ID"]}.pdf'
        if fname.exists():
            open_viewer(fname)
        else:
            print('No pdf linked to this entry')

    @bib_index_arg_check
    def do_link(self, args):
        '''Link bibtex entry with picked up document'''

        self.do_docpickup('')
        id_ = self._get_bibid(args)
        if id_ is None:
            print('Index out of range')
            return

        print(f'Bibtex entry: {config.Terminal.PURPLE + self.bibtex.entries[id_]["ID"] +  config.Terminal.END}')
        for key in ['title','author','year']:
            if key in self.bibtex.entries[id_]:
                print(f'{key}: {self.bibtex.entries[id_][key]}')
        opts_ = [file.name for file in self.new_links]
        questions = [
            inquirer.List('pdf',
                message='Shall be linked with which PDF?',
                choices=opts_ + ['NONE'],
                carousel=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        answer = answers['pdf']
        if answer == 'NONE':
            print('No PDF linked')
            return
        else:
            new_path = config.PAPERS_FOLDER / f'{self.bibtex.entries[id_]["ID"]}.pdf'
            os.rename(self.new_links[opts_.index(answer)], new_path)
            del self.new_links[opts_.index(answer)]
            print(f'{config.Terminal.GREEN + new_path.name + config.Terminal.END} added to paper database')


    def do_ads(self, args):
        '''Do a search query on the Harvard ADS database and add selected papers to the database. Download PDFs if possible'''

        if ads is None:
            print('ADS interface import failed')
            return 

        if len(args) == 0:
            print('No search query given')
            return 

        arg_dict = {}
        find_ret = 0
        find_pos = 0
        while True:
            eq_pos = args.find('=', find_pos)
            if eq_pos == -1:
                break
            key = args[find_pos:eq_pos].strip()
            if eq_pos+1 >= len(args):
                break

            if args[eq_pos+1] in ['"', "'"]:
                find_pos = args.find(args[eq_pos+1], eq_pos+2)
                if find_pos == -1:
                    raise Exception('No closing quotation mark on pattern')
                pattern = args[(eq_pos+2):find_pos]
            else:
                find_pos = args.find(' ', eq_pos)
                if find_pos == -1:
                    find_pos = len(args)
                pattern = args[(eq_pos+1):find_pos]

            arg_dict[key] = pattern

            if find_pos+1 >= len(args):
                break

        res_ = ads.get_bibtex_from_ADS(arg_dict)
        if res_ is None:
            return
        else:
            bib_database, bibcodes = res_

        bib.rename_bibtex(bib_database)
        #add non-duplicates
        _add = 0
        _skip = 0
        for in_entry in bib_database.entries:
            _exists = False
            for entry in self.bibtex.entries:
                if in_entry['ID'] == entry['ID']:
                    _exists = True
                if str(in_entry['title']) == str(entry['title']):
                    _exists = True

            if not _exists:
                self.bibtex.entries.append(in_entry)
                _add += 1
            else:
                _skip += 1
        if _skip > 0:
            print('Skipped {} duplicates'.format(_skip))
        print('Added {} entries'.format(_add))

        self.do_save('')

        ads.get_PDF_from_ADS(bibcodes, [entry['ID'] for entry in bib_database.entries])

        self.do_load('')


    def do_adsfill(self, args):
        '''Attempt to get pdfs for all bibtex entries generated by ads'''
        bibcodes = []
        bib_ids = []

        for entry in self.bibtex.entries:
            if 'adsurl' in entry:
                bibcode = entry['adsurl'].split('/')[-1]
                bibcode = bibcode.replace('}','')

                bibcodes.append(bibcode)
                bib_ids.append(entry['ID'])

        ads.get_PDF_from_ADS(bibcodes, bib_ids)
        self.do_load('')

    def setup(self):
        self.bibtex = None
        self.docs = None
        self.new_links = None
        self.current_bibtex = None
        self.limit = 20
        self.do_docpickup('')


    def do_exit(self, args):
        '''Quits the program.'''
        print('Quitting and saving')
        self.do_save('')
        raise SystemExit
    def do_quit(self, args):
        '''Quits the program.'''
        print('Quitting and saving')
        self.do_save('')
        raise SystemExit


Shell.do_bw = Shell.do_bibview

def run():
    prompt = Shell()
    prompt.prompt = '> '
    prompt.setup()
    prompt.do_load('')
    prompt.cmdloop('Starting prompt...')