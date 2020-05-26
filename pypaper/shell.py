
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
            _skip = 0
            _add = 0
            b = bib.load_bibtex(b_path)
            bib.rename_bibtex(b)
            #add non-duplicates
            for in_entry in b.entries:
                _exists = False
                for entry in self.bibtex.entries:
                    if in_entry['ID'] == entry['ID']:
                        _exists = True
                    if in_entry['title'] == entry['title']:
                        _exists = True

                if not _exists:
                    self.bibtex.entries.append(in_entry)
                    _add += 1
                else:
                    _skip += 1
            if _skip > 0:
                print('Skipped {} duplicates'.format(_skip))
            print('Added {} entires'.format(_add))
            os.rename(b_path, config.TRASH_FOLDER / b_path.name)

        if len(docs) == 0 and len(bibs) == 0:
            print('Pickup folder empty')
        else:
            self.do_save('')


    def do_save(self, args):
        '''Save bibtex file'''
        bib.save_bibtex(config.BIB_FILE, self.bibtex)


    def do_bibrm(self, args):
        '''Remove bibtex entry'''
        del self.bibtex.entries[self.current_bibtex[int(args)]]
        self.do_save('')


    def do_bibview(self, args):
        '''View bibtex entry'''
        id_ = self.current_bibtex[int(args)]
        entry = self.bibtex.entries[id_]
        print(config.Terminal.PURPLE + entry['ID'] +  config.Terminal.END)
        for key in entry:
            print(f'- {config.Terminal.BOLD + key + config.Terminal.END}: {entry[key]}')

    def do_id(self, args):
        '''Copy bibtex entry to clipboard'''
        id_ = self.current_bibtex[int(args)]
        entry = self.bibtex.entries[id_]

        data = entry['ID']
        cmd = ['xsel','-b','-i']
        subprocess.run(cmd, universal_newlines=True, input=data)
        print('Copied ID to clipboard')


    def do_clip(self, args):
        '''Copy bibtex entry to clipboard'''
        id_ = self.current_bibtex[int(args)]
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
        print(f'{len(self.current_bibtex)} entires in current list')
        if self.new_links is not None:
            print(f'{len(self.new_links)} picked up documents to link')
        if self.docs is not None:
            print(f'{len(self.docs)} documents in database')


    def do_load(self, args):
        '''Load bibtex file and list of papers'''
        self.bibtex = bib.load_bibtex(config.BIB_FILE)
        bib.rename_bibtex(self.bibtex)
        if len(self.bibtex.entries) > 20:
            self.current_bibtex = list(range(20))
        else:
            self.current_bibtex = list(range(len(self.bibtex.entries)))

        print('Bib load: {} entries loaded'.format(len(self.bibtex.entries)))
        self.docs = glob(str(config.PAPERS_FOLDER / '*.pdf'))
        self.docs = [pathlib.Path(p) for p in self.docs]

        print('DOCS load: {} papers found'.format(len(self.docs)))


    def do_list(self, args):
        '''Lists all unlinked documents in pickup'''
        if self.new_links is None:
            print('Nothing has been picked up')
            return
        for id_,file in enumerate(self.new_links):
             print(f'{id_:<4}: {file.parts[-1]}')


    def do_viewpdf(self, args):
        '''Views an picked up document'''
        if not args.strip().isnumeric():
            print('No valid document index given')
            return

        if self.new_links is None:
            print('Nothing has been picked up')
            return

        subprocess.run(
            [config.config['General']['viewer'], str(self.new_links[int(args)])],
            stdout=subprocess.DEVNULL,
        )

    def do_view(self, args):
        '''Views an picked up document'''
        if not args.strip().isnumeric():
            print('No valid document index given')
            return

        if self.new_links is None:
            print('Nothing has been picked up')
            return

        if doc is None:
            subprocess.run(
                [config.config['General']['viewer'], str(self.new_links[int(args)])],
                stdout=subprocess.DEVNULL,
            )
        else:
            lines = doc.parse_pdf(self.new_links[int(args)])
            title = string.capwords(lines[0])
            print(title)
            print('='*len(title))
            for i in range(10):
                print(lines[i])


    def do_trash(self, args):
        '''Moves a document to trash folder in database'''
        os.rename(self.new_links[int(args)], config.TRASH_FOLDER / self.new_links[int(args)].name)
        del self.new_links[int(args)]


    def do_bib(self, args):
        '''Lists all loaded bibtex entries in database'''
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
                        resh = re.search(pattern, entry[key])
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
        else:
            if len(self.current_bibtex) == 0:
                if len(self.bibtex.entries) > 20:
                    self.current_bibtex = list(range(20))
                else:
                    self.current_bibtex = list(range(len(self.bibtex.entries)))


        for id_, cid_ in enumerate(self.current_bibtex):
            entry = self.bibtex.entries[cid_]
            file_ = '   '
            for f in self.docs:
                if f.stem == entry["ID"]:
                    file_ = 'pdf'

            print(f'{id_:<4}[{file_}]: {entry["ID"]}')


    def do_open(self, args):
        '''Opens paper linked to bibtex entry'''
        if not args.strip().isnumeric():
            print('No valid bibtex index given')
            return

        id_ = self.current_bibtex[int(args)]
        fname = config.PAPERS_FOLDER / f'{self.bibtex.entries[id_]["ID"]}.pdf'
        if fname.exists():
            subprocess.run(
                [config.config['General']['viewer'], fname],
                stdout=subprocess.DEVNULL,
            )
        else:
            print('No pdf linked to this entry')


    def do_link(self, args):
        '''Link bibtex entry with picked up document'''
        if not args.strip().isnumeric():
            print('No valid bibtex index given')
            return

        self.do_docpickup('')
        id_ = self.current_bibtex[int(args)]

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
        if answers == 'NONE':
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
                if in_entry['title'] == entry['title']:
                    _exists = True

            if not _exists:
                self.bibtex.entries.append(in_entry)
                _add += 1
            else:
                _skip += 1
        if _skip > 0:
            print('Skipped {} duplicates'.format(_skip))
        print('Added {} entires'.format(_add))

        self.do_save('')

        ads.get_PDF_from_ADS(bibcodes, [entry['ID'] for entry in bib_database.entries])

        self.do_load('')


    def setup(self):
        self.bibtex = None
        self.docs = None
        self.new_links = None
        self.current_bibtex = None


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