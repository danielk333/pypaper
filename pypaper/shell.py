from cmd import Cmd
from glob import glob
import os
import pathlib
import subprocess
import re
import string

from . import config
from . import bib

try:
    from . import doc
except ImportError:
    doc = None

class Shell(Cmd):


    def do_pickup(self, args):
        '''Pickup bibtex files and pdf files to add to database'''
        docs = glob(str(config.PICKUP_FOLDER / '*.pdf'))
        docs = [pathlib.Path(p) for p in docs]

        self.new_links = docs

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
                if not _exists:
                    self.bibtex.entries.append(in_entry)
                    _add += 1
                else:
                    _skip += 1
            if _skip > 0:
                print('Skipped {} duplicates'.format(_skip))
            print('Added {} entires'.format(_add))
            os.remove(b_path)

        if len(docs) == 0 and len(bibs) == 0:
            print('Pickup folder empty')
        else:
            self.do_save('')


    def do_save(self, args):
        '''Save bibtex file'''
        bib.save_bibtex(config.BIB_FILE, self.bibtex)


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
        if self.new_links is None:
            print('Nothing has been picked up')
            return

        subprocess.run(
            [config.config['General']['viewer'], str(self.new_links[int(args)])],
            stdout=subprocess.DEVNULL,
        )

    def do_view(self, args):
        '''Views an picked up document'''
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

        if len(args) > 0:
            arg_list = [arg.split('=') for arg in args.split(' ')]
            self.current_bibtex = []
            for id_,entry in enumerate(self.bibtex.entries):
                add_ = False
                for key, pattern in arg_list:
                    add_ = add_ or re.search(pattern, entry[key]) is not None
                if add_:
                    self.current_bibtex.append(id_)

        for id_, cid_ in enumerate(self.current_bibtex):
            entry = self.bibtex.entries[cid_]
            file_ = '   '
            for f in self.docs:
                if f.stem == entry["ID"]:
                    file_ = 'pdf'

            print(f'{id_:<4}[{file_}]: {entry["ID"]} - {entry["title"]}')


    def do_open(self, args):
        '''Opens paper linked to bibtex entry'''
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
        bib_, doc_ = [int(arg) for arg in args.strip().split(' ')]
        id_ = self.current_bibtex[bib_]
        os.rename(self.new_links[doc_], config.PAPERS_FOLDER / f'{self.bibtex.entries[id_]["ID"]}.pdf')
        del self.new_links[doc_]


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


def run():
    prompt = Shell()
    prompt.prompt = '> '
    prompt.setup()
    prompt.do_load('')
    prompt.cmdloop('Starting prompt...')