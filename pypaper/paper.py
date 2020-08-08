
#Python standard
from glob import glob
import os
import pathlib
import subprocess
import re
import string
import curses
import argparse

#Third party
import bibtexparser

#Local
from . import config
from . import bib
from .application import App, Key, BrowseDisplay, Shell

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


class ListBib(BrowseDisplay):

    def __init__(self, *args, **kwargs):
        self.bib_key_color = kwargs.pop('bib_key_color')
        self.bib_item_color = kwargs.pop('bib_item_color')
        super().__init__(*args, **kwargs)

        self.actions[':'] = self.shell
        self.actions['/'] = self.search
        self.actions['q'] = self.exit
        self.actions[Key.RETURN] = self.shell

    def search(self):
        self.data = 'shell search'
        return False

    def exit(self):
        self.data = 'exit'
        return False

    def shell(self):
        self.data = 'shell'
        return False

    def draw_item(self, item):
        self.display_window.border()
        y, x = self.display_window.getmaxyx()

        row = 0
        for i, key_ in enumerate(item.keys()):
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

    def __init__(self, colors):
        super().__init__(colors)

        self.bibtex = None
        self.docs = None

        self.cmdbox_h = 3
        self.search_h = 1
        self.output_h = 1

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
        self.states['cmd'].clear_cmd()


    def resize(self):
        bib_h, bib_w = self.bib_size
        self.states['bib'].window.mvwin(self.search_h, 0)
        self.states['bib'].window.resize(bib_h, bib_w)
        
        display_h, display_w = self.display_size
        self.states['bib'].display_window.mvwin(self.output_h, bib_w)
        self.states['bib'].display_window.resize(display_h, display_w)
        
        cmd_h, cmd_w = self.cmd_size
        self.states['cmd'].window.mvwin(bib_h + self.search_h, 0)
        self.states['cmd'].window.resize(cmd_h, cmd_w )
        

    @property
    def cmd_size(self):
        return self.cmdbox_h, curses.COLS

    @property
    def bib_size(self):
        bib_h = curses.LINES - self.cmdbox_h - self.search_h
        bib_w = int(curses.COLS*config.config['General'].getfloat('split-size'))
        return bib_h, bib_w

    @property
    def display_size(self):
        bib_h, bib_w = self.bib_size

        display_h = curses.LINES - self.cmdbox_h - self.output_h
        display_w = curses.COLS - bib_w
        return display_h, display_w

    def do_load(self, args=None):
        '''Load bibtex file and list of papers'''
        self.bibtex = bib.load_bibtex(config.BIB_FILE)
        if 'bib' in self.states:
            self.states['bib'].subset = list(range(len(self.bibtex.entries)))
        self.docs = glob(str(config.PAPERS_FOLDER / '*.pdf'))
        self.docs = [pathlib.Path(p) for p in self.docs]

        return 'cmd'


    def do_list(self, args):
        return 'bib'


    def do_shell(self, args):
        if len(args.strip()) > 0:
            self.states['cmd'].enter_command(args)
        return 'cmd'


    def do_exit(self, args):
        return 'exit'


    # def list_bib(self, limit):
    #     if len(self.bib_inds) > limit:
    #         display_bibtex = self.bib_inds[self.offset:(self.offset+limit)]
    #     else:
    #         display_bibtex = self.bib_inds

    #     strs_ = [None]*len(display_bibtex)
    #     for id_, cid_ in enumerate(display_bibtex):
    #         entry = self.bibtex.entries[cid_]
    #         file_ = '   '
    #         for f in self.docs:
    #             if f.stem == entry["ID"]:
    #                 file_ = 'pdf'

    #         strs_[id_] = f'{cid_:<4}[{file_}]: {entry["ID"]}'
    #     return strs_


    # def draw_bib(self, bib_id=None):
    #     self.bib_window.erase()
    #     self.bib_window.bkgd(' ', self.color('background'))
        
    #     y, x = self.bib_window.getmaxyx()
    #     limit = y - 2

    #     lines = self.list_bib(limit)
    #     self.screen.addnstr(0, 1, ' '*(y-1), self.bib_w-1, self.color('search'))
    #     self.screen.addnstr(0, 1, self.search, self.bib_w-1, self.color('search'))
    #     self.screen.noutrefresh()

    #     for i in range(len(lines)):
    #         attrs = self.color('bib-line')
    #         if bib_id is not None:
    #             if bib_id - self.offset == i:
    #                 attrs = self.color('bib-line-select')

    #         self.bib_window.addnstr(i+1, 1, lines[i], self.bib_w-2, attrs)
        
    #     self.bib_window.border()
    #     self.bib_window.refresh()




    # def draw_cmd(self):
    #     self.cmdwin.bkgd(' ', self.color('background'))

    #     self.cmdwin.addstr(1,1,' '*len(self.prompt), self.color('prompt'))
        
    #     y, x = self.cmdwin.getmaxyx()
    #     start_ch = 1 + len(self.prompt)
    #     self.cmdwin.addstr(1, start_ch, ' '*(x - start_ch - 1), self.color('command'))
        
    #     self.cmdwin.border()
    #     self.cmdwin.refresh()



    # def setup(self):
    #     self.bibtex = None
    #     self.docs = None
    #     self.current_docs = None
    #     self.current_bibtex = None

    #     self.prompt = ': '
    #     self.offset = 0

    #     self.cmd_history = []
    #     self.search = '(No search applied)'
    #     self.output = ''

    #     self.use_colors = config.config['General'].getboolean('use colors')

    #     self.screen = curses.initscr()
    #     curses.noecho()

    #     self.cmdbox_h = 3
    #     self.search_h = 1
    #     self.output_h = 1

    #     if curses.has_colors() and self.use_colors:
    #         curses.start_color()
    #         self.setup_colors()

    #     curses_ui()


    #     self.screen.bkgd(' ', self.color('background'))
    #     self.screen.noutrefresh()

    #     self.bib_h = curses.LINES - self.cmdbox_h - self.search_h
    #     self.bib_w = int(curses.COLS*config.config['General'].getfloat('split-size'))
    #     self.bib_window = curses.newwin(self.bib_h, self.bib_w, self.search_h, 0)
    #     self.bib_window.keypad(True)

    #     self.display_h = curses.LINES - self.cmdbox_h - self.output_h
    #     self.display_w = curses.COLS - self.bib_w
    #     self.display_window = curses.newwin(self.display_h, self.display_w, self.output_h, self.bib_w)
    #     self.display_window.keypad(True)

    #     self.cmdwin = curses.newwin(self.cmdbox_h, curses.COLS, self.bib_h + self.search_h, 0)
    #     self.cmdwin.keypad(True)

    #     self.do_load()
    #     self.draw_init()
    #     self.draw_cmd()

    #     curses.doupdate()

    # def draw_init(self):
    #     if len(self.bib_inds) > 0:
    #         bid = 0
    #     else:
    #         bid = None
    #     self.draw_bib(bid)
    #     self.draw_display(bid)


    # def get_command(self, prefill = ''):

    #     self.cmdwin.addstr(1,1,self.prompt, self.color('prompt'))
    #     self.cmdwin.addstr(1,1+len(self.prompt), prefill, self.color('command'))
    #     curses_edit()
    #     cmd_enter = Edit(self.cmdwin, self.cmd_history, len(self.prompt) + 1, self.color('command'), start_offset = len(prefill))
    #     execute = cmd_enter.run()
    #     curses_ui()
    #     if execute:
    #         cmd = cmd_enter.content().strip()
    #         self.draw_cmd()
    #     else:
    #         cmd = ''
    #     self.cmdwin.addstr(1,1,' '*len(self.prompt), self.color('prompt'))
    #     return cmd



    # def do_search(self, args):
    #     '''Lists selected bibtex entries in database, syntax: --tag "" [field]=[regex] &/| [field]=[regex]...'''

    #     parser = argparse.ArgumentParser(description='Process some integers.')
    #     self.search = args

    #     tags = []
    #     if len(args) > 0:
    #         find_limit = args.find('--tag', 0)
    #         if find_limit != -1:
    #             find_space = args.find(' ', find_limit+6)
    #             if find_space == -1:
    #                 tags = args[(find_limit+6):].split(',')
    #                 find_space = len(args)
    #             else:
    #                 tags = args[(find_limit+6):find_space].split(',')

    #             args = args.replace(args[find_limit:find_space], '')
        
    #     args = args.strip()

    #     if len(args) > 0:
    #         arg_list = []
    #         operators = []
    #         find_ret = 0
    #         find_pos = 0

    #         while True:
    #             eq_pos = args.find('=', find_pos)
    #             if eq_pos == -1:
    #                 break
    #             key = args[find_pos:eq_pos].strip()
    #             if eq_pos+1 >= len(args):
    #                 arg_list.append([len(arg_list), key, ''])
    #                 break

    #             if args[eq_pos+1] in ['"', "'"]:
    #                 find_pos = args.find(args[eq_pos+1], eq_pos+2)
    #                 if find_pos == -1:
    #                     raise Exception('No closing quotation mark on pattern')
    #                 pattern = args[(eq_pos+2):find_pos]
    #                 find_pos += 1
    #             else:
    #                 find_pos = args.find(' ', eq_pos)
    #                 if find_pos == -1:
    #                     find_pos = len(args)
    #                 pattern = args[(eq_pos+1):find_pos]

    #             arg_list.append([len(arg_list), key, pattern])

    #             if find_pos+1 >= len(args):
    #                 break
    #             else:
    #                 operators.append(args[find_pos+1])
    #                 find_pos += 3

    #         self.bib_inds = []
    #         for id_,entry in enumerate(self.bibtex.entries):
    #             add_ = None
    #             for arg_id, key, pattern in arg_list:
    #                 if key in entry:
    #                     resh = re.search(pattern, str(entry[key]))
    #                     if add_ is None:
    #                         add_ = resh is not None
    #                     else:
    #                         operator = operators[arg_id-1]
    #                         if operator == '&':
    #                             add_ = add_ and resh is not None
    #                         elif operator == '|':
    #                             add_ = add_ or resh is not None
    #             if add_ is None:
    #                 add_ = False
                
    #             if len(tags) > 0:
    #                 if 'tags' in entry:
    #                     tag_ex_ = False
    #                     etags = entry['tags'].split(',')
    #                     for tag in tags:
    #                         if tag in etags:
    #                             tag_ex_ = True
    #                             break
    #                     add_ = add_ and tag_ex_
    #                 else:
    #                     add_ = False

    #             if add_:
    #                 self.bib_inds.append(id_)

    #     else:
    #         if len(tags) > 0:
    #             self.bib_inds = []
    #             for id_,entry in enumerate(self.bibtex.entries):
    #                 tag_ex_ = False
    #                 if 'tags' in entry:
    #                     etags = entry['tags'].split(',')
    #                     for tag in tags:
    #                         if tag in etags:
    #                             tag_ex_ = True
    #                             break
    #                 if tag_ex_:
    #                     self.bib_inds.append(id_)

    #     self.output = f'{len(self.bib_inds)} Matches'
    #     self.draw_init()


def run():
    app = Pypaper(colors = config.colors)

    try:
        app.run('bib')
    except (Exception, KeyboardInterrupt) as excep:
        app.restore_curses()
        raise excep
    app.restore_curses()
