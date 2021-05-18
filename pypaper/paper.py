
#Python standard
from glob import glob
import os
import pathlib
import subprocess
import re
import string
import curses
import argparse
import json

#Third party
import bibtexparser

#Local
from . import config
from . import bib
from .application import App, Key, BrowseDisplay, Shell, Browse, Popup

try:
    from . import doc
except ImportError:
    doc = None

try:
    from . import ads
except Exception:
    ads = None


def open_viewer(path):
    subprocess.Popen(
        [config.config['General']['viewer'], str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

class ListNewDocs(Browse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bib_ind_linking = None

        self.actions[':'] = self.shell
        self.actions['/'] = lambda: self.shell('search-picked-up ')
        self.actions['o'] = lambda: self.execute(f'open-picked-up {self.index}')
        self.actions[Key.RETURN] = lambda: self.execute(f'link-picked-up {self.index}')
        self.actions[Key.ESCAPE] = self.esc


    def esc(self):
        self.data = 'list'
        return False


    def execute(self, arg):
        self.data = arg
        return False


    def shell(self, arg = ''):
        self.data = f'shell {arg}'
        return False


class Help(Popup):
    def __init__(self, *args, **kwargs):
        self.action_color = kwargs.pop('action_color')
        super().__init__(*args, **kwargs)
        self.content = [x for x in self.content if x[0] != '<resize>']
        self.key_size = max([len(x[0]) for x in self.content])

    def draw_line(self, row_n, line, max_length, start_ch):
        action, help_str = line
        if action.startswith('^'):
            action = 'Ctrl+' + action[1:]
        action = action.replace('<', '').replace('>', '')
        action = f'{action:<{self.key_size}} '
        self.window.addnstr(row_n, start_ch, action, max_length, self.action_color)
        self.window.addnstr(row_n, start_ch+len(action), help_str, max_length-len(action), self.color)


class ListBib(BrowseDisplay):

    def __init__(self, *args, **kwargs):
        self.bib_key_color = kwargs.pop('bib_key_color')
        self.bib_item_color = kwargs.pop('bib_item_color')
        super().__init__(*args, **kwargs)

        self.actions[':'] = self.shell
        self.actions['/'] = lambda: self.shell('search ')
        self.actions['q'] = self.exit
        self.actions['o'] = lambda: self.execute(f'open {self.index}')
        self.actions['d'] = self.remove_item
        self.actions['l'] = lambda: self.execute(f'link {self.index}')
        self.actions['c'] = lambda: self.execute(f'clip {self.index}')
        self.actions[Key.RETURN] = self.shell

        self.help[':'] = 'Enter command mode'
        self.help['/'] = 'Enter search'
        self.help['q'] = 'Exit application'
        self.help['o'] = 'Open PDF'
        self.help['d'] = 'Remove item from selection'
        self.help['l'] = 'Link bibtex entry to picked up PDF'
        self.help['c'] = 'Copy bibtex entry to clipboard'
        self.help[Key.RETURN] = 'Enter command mode'


    def execute(self, arg):
        self.data = arg
        return False

    def exit(self):
        self.data = 'exit'
        return False

    def shell(self, arg = ''):
        self.data = f'shell {arg}'
        return False

    def remove_item(self):
        del self.subset[self.index]
        if self.index >= len(self.subset):
            self.index = len(self.subset) - 1
        return True


    def draw_item(self, item):
        self.display_window.border()
        y, x = self.display_window.getmaxyx()
        y -= 1

        keys = list(item.keys())

        if 'ID' in keys: keys.remove('ID')
        if 'pdf' in keys: keys.remove('pdf')

        row = 0
        for i, key_ in enumerate(keys):
            row += 1
            key = key_ + ': '
            if row > y-1:
                break
            self.display_window.addnstr(row, 1, key, x-2, self.bib_key_color)
            max_len = x-2-len(key)
            entry_str = str(item[key_])

            #some cleaning
            entry_str = entry_str.replace('\n', ' ')

            if len(entry_str) <= max_len:
                self.display_window.addstr(row, 1+len(key), entry_str, self.bib_item_color)
            else:
                words = entry_str.split(' ')
                wid = 0
                value = ''
                for wid, word in enumerate(words):
                    if len(word) > max_len:
                        value += word[:(max_len - len(value) - 1)] + '-'
                        self.display_window.addstr(row, 1+len(key), value, self.bib_item_color)
                        row += 1
                        value = word[(max_len - len(value) - 1):] + ' '
                    else:
                        if len(value) + len(word) + 1 > max_len:
                            try:
                                self.display_window.addstr(row, 1+len(key), value, self.bib_item_color)
                            except:
                                raise Exception(str((row, 1+len(key), value, self.bib_item_color)))
                            
                            row += 1
                            if row > y-1:
                                break
                            value = ''
                        value += word + ' '
                if row > y-1:
                    break
                self.display_window.addstr(row, 1+len(key), value, self.bib_item_color)


class Pypaper(App):

    def load_state(self):
        if not config.DATA_FILE.is_file():
            return 
        with open(config.DATA_FILE, 'r') as f:
            data = json.load(f)
            self.states['cmd'].history = data['history']
            self.search = data['search']
            self.states['bib'].subset = data['search-results']
            if self.states['bib'].subset is None:
                self.states['bib'].subset = list(range(len(self.bibtex.entries)))


    def save_state(self):
        hmax = config.config['General'].getint('save-history')
        with open(config.DATA_FILE, 'w') as f:
            data = {
                'history': self.states['cmd'].history[:hmax],
                'search': self.search,
                'search-results': self.states['bib'].subset,
            }
            json.dump(data, f)


    def __init__(self, colors):
        super().__init__(colors)

        self.bibtex = None
        self.docs = None

        self.search = ''

        self.cmdbox_h = 3
        self.search_h = 1
        self.output_h = 1

        self.new_doc_paths = []

        bib_h, bib_w = self.bib_size
        bib_window = curses.newwin(bib_h, bib_w, self.search_h, 0)
        bib_window.keypad(True)

        display_h, display_w = self.display_size
        display_window = curses.newwin(display_h, display_w, self.output_h, bib_w)
        display_window.keypad(True)

        cmd_h, cmd_w = self.cmd_size
        cmd_window = curses.newwin(cmd_h, cmd_w, bib_h + self.search_h, 0)
        cmd_window.keypad(True)

        self.do_load()

        self.states['bib'] = ListBib(
            window = bib_window, 
            display_window = display_window, 
            lst = self.bibtex.entries, 
            fmt = config.config['General']['format'], 
            color = self.color('standard'), 
            select_color = self.color('bib-line-select'),
            pg_step = config.config['General'].getint('page-key-step'), 
            margin = 1, 
            border=True,
            bib_key_color = self.color('bib-key'),
            bib_item_color = self.color('bib-item'),
        )
        self.states['bib'].subset = list(range(len(self.bibtex.entries)))

        self.states['cmd'] = Shell(
            window = cmd_window, 
            prompt = ': ', 
            prompt_color = self.color('prompt'), 
            command_color = self.color('command'), 
            border=True, 
            prompt_line = 1,
        )

        self.states['new_docs'] = ListNewDocs(
            window = display_window, 
            lst = [], 
            fmt = '{index:<4}: {name}', 
            color = self.color('standard'), 
            select_color = self.color('bib-line-select'),
            pg_step = config.config['General'].getint('page-key-step'), 
            margin = 1, 
            border=True,
        )

        for state in self.states:
            self.states[state].actions[Key.RESIZE] = lambda: self.resize()

        self.states['bib'].actions['h'] = lambda: self.help_state('bib')
        self.states['new_docs'].actions['h'] = lambda: self.help_state('new_docs')

        self.states['bib'].help['h'] = 'Display help'
        self.states['new_docs'].help['h'] = 'Display help'

        self.load_state()
        self.do_docpickup()


    def draw_output(self):
        bib_h, bib_w = self.bib_size
        display_h, display_w = self.display_size
        self.screen.addstr(0, bib_w, ' '*(display_w-1), self.color('output'))
        self.screen.addnstr(0, bib_w, self.output, display_w-1, self.color('output'))
        self.screen.refresh()

    def draw_search(self):
        bib_h, bib_w = self.bib_size
        self.screen.addstr(0, 0, ' '*bib_w, self.color('search'))
        self.screen.addnstr(0, 1, self.search, bib_w-1, self.color('search'))
        self.screen.refresh()

    def draw_init(self):
        self.states['bib'].draw()
        self.states['cmd'].clear_cmd()
        self.states['cmd'].draw()
        self.draw_output()
        self.draw_search()
        curses.doupdate()

    def postcmd(self, state, cmd):
        self.draw_output()
        super().postcmd(state, cmd)


    def resize(self):
        if not curses.is_term_resized(self.LINES, self.COLS):
            return
        self.LINES, self.COLS = self.screen.getmaxyx()
        curses.resizeterm(self.LINES, self.COLS)

        bib_h, bib_w = self.bib_size
        self.states['bib'].window.resize(bib_h, bib_w)
        self.states['bib'].window.mvwin(self.search_h, 0)
        
        display_h, display_w = self.display_size
        self.states['bib'].display_window.resize(display_h, display_w)
        self.states['bib'].display_window.mvwin(self.output_h, bib_w)
        
        cmd_h, cmd_w = self.cmd_size
        self.states['cmd'].window.resize(cmd_h, cmd_w)
        self.states['cmd'].window.mvwin(bib_h + self.search_h, 0)

        self.states['bib'].draw()
        self.states['cmd'].enter_command(self.states['cmd'].get_command())

        self.draw_search()
        self.draw_output()
        self.screen.refresh()
        curses.doupdate()
        

    @property
    def cmd_size(self):
        return self.cmdbox_h, self.COLS-1

    @property
    def bib_size(self):
        bib_h = self.LINES - self.cmdbox_h - self.search_h
        bib_w = int(self.COLS*config.config['General'].getfloat('split-size'))
        return bib_h, bib_w

    @property
    def display_size(self):
        bib_h, bib_w = self.bib_size

        display_h = self.LINES - self.cmdbox_h - self.output_h
        display_w = self.COLS - bib_w
        return display_h, display_w


    def help_state(self, state):
        help_dict = self.states[state].get_help()
        max_len = max([len(key) for key in help_dict])
        help_screen = Help(
            window = self.states['bib'].display_window, 
            content = list(help_dict.items()),
            color = self.color('bib-item'), 
            action_color = self.color('bib-key'), 
            border = True,
        )
        help_screen.data = state
        help_screen.draw()
        key = Key.read(help_screen.window)
        del help_screen
        self.states[state].draw()



    #### DO COMMANDS ####

    def do_help(self, args):
        help_dict = {}
        for attr in dir(self):
            if len(args) == 0:
                if attr.startswith('do_'):
                    h_ = getattr(self, attr).__doc__
                    if h_ is None:
                        h_ = 'No help found'
                    help_dict[attr[3:]] = h_.split('\n')[0]
            else:
                if attr.startswith('do_'):
                    if attr[3:] == args:
                        help_dict[attr[3:]] = getattr(self, attr).__doc__

        help_screen = Help(
            window = self.states['bib'].display_window, 
            content = list(help_dict.items()),
            color = self.color('bib-item'), 
            action_color = self.color('bib-key'), 
            border = True,
        )
        help_screen.data = 'cmd'
        help_screen.draw()
        key = Key.read(help_screen.window)
        del help_screen
        self.states['bib'].draw()
        self.states['cmd'].draw()

    def do_clip(self, args):
        '''Copy bibtex entry to clipboard'''
        entry = self.bibtex.entries[self.states['bib'].subset[int(args)]]

        bib_database = bibtexparser.bibdatabase.BibDatabase()
        bib_database.entries = [entry]

        data = bibtexparser.dumps(bib_database)
        cmd = ['xsel','-b','-i']
        subprocess.run(cmd, universal_newlines=True, input=data)
        self.output = 'Copied bibtex entry to clipboard'


    def do_export(self, args):
        if len(args) == 0:
            fout = None
        else:
            fout = pathlib.Path(args)

        bib_database = bibtexparser.bibdatabase.BibDatabase()
        bib_database.entries = []
        for ind in self.states['bib'].subset:
            bib_database.entries.append(self.bibtex.entries[ind])

        data = bibtexparser.dumps(bib_database)
        if fout is None:
            cmd = ['xsel','-b','-i']
            subprocess.run(cmd, universal_newlines=True, input=data)
            self.output = 'Copied bibtex list to clipboard'
        else:
            with open(fout, 'w') as f:
                f.write(data)
            self.output = f'Wrote bibtex list to {str(fout)}'



    def do_link(self, args):
        if len(self.states['new_docs'].lst) == 0:
            self.output = 'No PDFs picked up'
            return 'bib'
        self.prepare_picked_up(link=int(args))
        return 'new_docs'

    def do_link_picked_up(self, args):
        if self.states['new_docs'].bib_ind_linking is None:
            self.output = 'No bibtex entry chosen, PDF not linked'
            return None

        fname = f'{self.bibtex.entries[self.states["new_docs"].bib_ind_linking]["ID"]}.pdf'
        new_path = config.PAPERS_FOLDER / fname
        if new_path.is_file():
            new_path.unlink()

        doc_ind = int(args)

        os.rename(self.new_doc_paths[doc_ind], new_path)
        del self.new_doc_paths[doc_ind]
        self.output = f'{new_path.name} added to paper database'

        self.docs.append(new_path)
        self.bibtex.entries[self.states["new_docs"].bib_ind_linking]['pdf'] = 'pdf'

        self.states['bib'].draw()

        return 'bib'


    def prepare_picked_up(self, link=None):
        if link is not None:
            self.states['new_docs'].bib_ind_linking = self.states['bib'].subset[link]
        else:
            self.states['new_docs'].bib_ind_linking = None
        self.states['new_docs'].subset = list(range(len(self.states['new_docs'].lst)))
        self.states['new_docs'].index = 1
        self.states['new_docs'].draw()


    def do_pickedup(self,args):
        if len(self.states['new_docs'].lst) > 0:
            self.prepare_picked_up()
            return 'new_docs'
        else:
            return None


    def do_docpickup(self, args=None):
        '''pdf files to add to database'''
        docs = glob(str(config.PICKUP_FOLDER / '*.pdf'))
        docs = [pathlib.Path(p) for p in docs]

        self.new_doc_paths = docs
        self.states['new_docs'].lst = [dict(name=doc.name) for doc in docs]

        return 'cmd'


    def do_pickup(self, args):
        '''Pickup bibtex files and pdf files to add to database'''

        self.do_docpickup()

        bibs = glob(str(config.PICKUP_FOLDER / '*.bib'))
        bibs = [pathlib.Path(p) for p in bibs]

        _add = 0
        if len(bibs) > 0:
            b = bib.load_bibtex(bibs)
            _skip = 0
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
                    if (config.PAPERS_FOLDER / f'{in_entry["ID"]}.pdf').is_file():
                        in_entry['pdf'] = 'pdf'
                    else:
                        in_entry['pdf'] = '   '
                    self.bibtex.entries.append(in_entry)
                    _add += 1
                else:
                    _skip += 1

            _add_str = 0
            for key in b.strings:
                if key not in self.bibtex.strings:
                    self.bibtex.strings[key] = b.strings[key]
                    _add_str += 1

            for b_path in bibs:
                os.rename(b_path, config.TRASH_FOLDER / b_path.name)

        if len(self.states['new_docs'].lst) == 0 and len(bibs) == 0:
            self.output = 'Pickup folder empty'
        else:
            self.output = f'Picked up {_add} bibs, {len(self.states["new_docs"].lst)} docs'
            if _add > 0:
                self.do_save('')
        return 'cmd'


    def do_save(self, args=None):
        '''Save bibtex file'''
        bib.save_bibtex(config.BIB_FILE, self.bibtex)
        return 'cmd'


    def refresh_docs(self):
        for entry in self.bibtex.entries:
            if (config.PAPERS_FOLDER / f'{entry["ID"]}.pdf').is_file():
                entry['pdf'] = 'pdf'
            else:
                entry['pdf'] = '   '


    def do_load(self, args=None):
        '''Load bibtex file and list of papers'''
        self.bibtex = bib.load_bibtex(config.BIB_FILE)
        if 'bib' in self.states:
            self.states['bib'].subset = list(range(len(self.bibtex.entries)))
        self.docs = glob(str(config.PAPERS_FOLDER / '*.pdf'))
        self.docs = [pathlib.Path(p) for p in self.docs]

        self.refresh_docs()

        self.output = f'{len(self.bibtex.entries)} ({len(self.docs)} pdfs) bibtex entries loaded'

        return 'cmd'


    def do_open_picked_up(self, args):
        '''Opens un-linked paper in pickup folder'''
        args = args.strip()
        if len(args) == 0:
            ind = self.states['new_docs'].index
        else:
            try:
                ind = int(args)
            except ValueError:
                self.output = f'Cannot convert "{args}" to index'
                return 'bib'

        id_ = self.states['new_docs'].subset[ind]

        open_viewer(self.new_doc_paths[id_])
        return 'new_docs'



    def do_open(self, args):
        '''Opens paper linked to bibtex entry'''
        args = args.strip()
        if len(args) == 0:
            ind = self.states['bib'].index
        else:
            try:
                ind = int(args)
            except ValueError:
                self.output = f'Cannot convert "{args}" to index'
                return 'bib'

        id_ = self.states['bib'].subset[ind]

        fname = config.PAPERS_FOLDER / f'{self.bibtex.entries[id_]["ID"]}.pdf'
        if fname.is_file():
            open_viewer(fname)
            return 'bib'
        else:
            self.output = 'No pdf linked to this entry'
            return 'bib'

    def do_list(self, args):
        self.states['bib'].draw()
        return 'bib'

    def do_shell(self, args):
        if len(args.strip()) > 0:
            self.states['cmd'].enter_command(args)
        return 'cmd'

    def do_quit(self, args):
        self.do_exit()

    def do_exit(self, args):
        self.save_state()
        self.do_save()
        return 'exit'

    def do_search(self, args):
        '''Lists selected bibtex entries in database, syntax: --tag [tag] --pdf [field]=[regex] &/| [field]=[regex]...'''

        self.search = args
        if len(args.strip()) == 0:
            self.states['bib'].subset = list(range(len(self.bibtex.entries)))
            self.output = f'Listing all entries'
            self.states['bib'].draw()
            self.draw_search()
            return 'bib'

        filter_pdf = False
        if len(args) > 0:
            find_limit = args.find('--pdf', 0)
            if find_limit != -1:
                args = args.replace('--pdf', '')
                args = args.strip()
                filter_pdf = True

        tags = []
        if len(args) > 0:
            find_limit = args.find('--tag', 0)
            if find_limit != -1:
                find_space = args.find(' ', find_limit+6)
                if find_space == -1:
                    tags = args[(find_limit+6):].split(',')
                    find_space = len(args)
                else:
                    tags = args[(find_limit+6):find_space].split(',')

                args = args.replace(args[find_limit:find_space], '')

        args = args.strip()

        bib_inds = None

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

            bib_inds = []
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
                if filter_pdf:
                    if entry['pdf'] != 'pdf':
                        add_ = False
                if add_ is None:
                    add_ = False
                
                if len(tags) > 0:
                    if 'tags' in entry:
                        tag_ex_ = False
                        etags = entry['tags'].split(',')
                        for tag in tags:
                            if tag in etags:
                                tag_ex_ = True
                                break
                        add_ = add_ and tag_ex_
                    else:
                        add_ = False

                if add_:
                    bib_inds.append(id_)

        else:
            if len(tags) > 0 or filter_pdf:
                bib_inds = []
                for id_,entry in enumerate(self.bibtex.entries):
                    tag_ex_ = False
                    if 'tags' in entry:
                        etags = entry['tags'].split(',')
                        for tag in tags:
                            if tag in etags:
                                tag_ex_ = True
                                break
                    if len(tags) == 0:
                        if entry['pdf'] == 'pdf':
                            tag_ex_ = True
                    else:
                        if filter_pdf:
                            if entry['pdf'] != 'pdf':
                                tag_ex_ = False
                    if tag_ex_:
                        bib_inds.append(id_)

        
        if bib_inds is not None:
            self.states['bib'].subset = bib_inds
            self.states['bib'].reset_selected()
            self.output = f'{len(bib_inds)} Matches'
            self.states['bib'].draw()
            self.draw_search()
        return 'bib'


def run():
    app = Pypaper(colors = config.colors)

    try:
        app.run('bib')
    except (Exception, KeyboardInterrupt) as excep:
        app.restore_curses()
        raise excep
    app.restore_curses()
