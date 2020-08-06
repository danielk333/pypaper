
#Python standard
from glob import glob
import os
import pathlib
import subprocess
import re
import string
import curses

#Third party
import bibtexparser

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


def curses_ui():
    try:
        curses.curs_set(0)
    except:
        pass

def curses_edit():
    try:
        curses.curs_set(1)
    except:
        pass


def open_viewer(path):
    subprocess.Popen(
        [config.config['General']['viewer'], str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class Key:
    SPECIAL = {'<backspace>': '⌫',  # ⌫
               '<del>': '⌦',
               '<ins>': '⎀',
               '<left>': '→',
               '<right>': '←',
               '<up>': '↑',
               '<down>': '↓',
               '<home>': 'Home',
               '<end>': 'End',
               '<escape>': '⎋',
               '<return>': '⏎',  # ↵ ↲
               '<pgup>': 'PgUp',  # ⇞
               '<pgdn>': 'PgDn',  # ⇟
               '<space>': '␣',
               '<tab>': '⇥',
               '<f1>': 'F1',
               '<f2>': 'F2',
               '<f3>': 'F3',
               '<f4>': 'F4',
               '<f5>': 'F5',
               '<f6>': 'F6',
               '<f7>': 'F7',
               '<f8>': 'F8',
               '<f9>': 'F9',
               '<f10>': 'F10',
               '<f11>': 'F11',
               '<f12>': 'F12',
               }
    BACKSPACE = '<backspace>'
    DELETE = '<del>'
    LEFT = '<left>'
    RIGHT = '<right>'
    UP = '<up>'
    DOWN = '<down>'
    PGUP = '<pgup>'
    PGDN = '<pgdn>'
    HOME = '<home>'
    END = '<end>'
    RETURN = '<return>'
    ESCAPE = '<escape>'
    SPACE = '<space>'
    TAB = '<tab>'
    F1 = '<f1>'
    F2 = '<f2>'
    F3 = '<f3>'
    F4 = '<f4>'
    F5 = '<f5>'
    F6 = '<f6>'
    F7 = '<f7>'
    F8 = '<f8>'
    F9 = '<f9>'
    F10 = '<f10>'
    F11 = '<f11>'
    F12 = '<f12>'

    def __init__(self, value, special=False):
        self.value = value
        self.special = special

    @classmethod
    def read(cls, stdscr):
        try:
            value = stdscr.get_wch()
            return Key.parse(value)
        except (KeyboardInterrupt, curses.error):
            return Key('C', special=True)
        except EOFError:
            return Key('D', special=True)

    @classmethod
    def parse(cls, value):
        if value == curses.KEY_BACKSPACE:
            return Key(Key.BACKSPACE, True)
        elif value == curses.KEY_DC:
            return Key(Key.DELETE, True)
        elif value == curses.KEY_LEFT:
            return Key(Key.LEFT, True)
        elif value == curses.KEY_RIGHT:
            return Key(Key.RIGHT, True)
        elif value == curses.KEY_UP:
            return Key(Key.UP, True)
        elif value == curses.KEY_DOWN:
            return Key(Key.DOWN, True)
        elif value == curses.KEY_END:
            return Key(Key.END, True)
        elif value == curses.KEY_HOME:
            return Key(Key.HOME, True)
        elif value == curses.KEY_NPAGE:
            return Key(Key.PGDN, True)
        elif value == curses.KEY_PPAGE:
            return Key(Key.PGUP, True)
        elif value == curses.KEY_F1:
            return Key(Key.F1, True)
        elif value == curses.KEY_F2:
            return Key(Key.F2, True)
        elif value == curses.KEY_F3:
            return Key(Key.F3, True)
        elif value == curses.KEY_F4:
            return Key(Key.F4, True)
        elif value == curses.KEY_F5:
            return Key(Key.F5, True)
        elif value == curses.KEY_F6:
            return Key(Key.F6, True)
        elif value == curses.KEY_F7:
            return Key(Key.F7, True)
        elif value == curses.KEY_F8:
            return Key(Key.F8, True)
        elif value == curses.KEY_F9:
            return Key(Key.F9, True)
        elif value == curses.KEY_F10:
            return Key(Key.F10, True)
        elif value == curses.KEY_F11:
            return Key(Key.F11, True)
        elif value == curses.KEY_F12:
            return Key(Key.F12, True)
        elif isinstance(value, int):
            # no idea what key that is
            return Key('', True)
        elif isinstance(value, str):
            try:
                ctrlkey = str(curses.unctrl(value), 'ascii')
            except OverflowError:
                # no idea what key that is
                return Key('', True)

            if value in "\n\r":
                return Key(Key.RETURN, special=True)

            if ctrlkey in ['^H', '^?']:
                return Key(Key.BACKSPACE, special=True)

            if ctrlkey == '^[':
                return Key(Key.ESCAPE, True)

            if ctrlkey != value:
                return Key(ctrlkey[1:], True)
            else:
                return Key(value)

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        if isinstance(other, Key):
            return self.value == other.value and self.special == other.special
        elif isinstance(other, str):
            return str(self) == other
        elif isinstance(other, bytes):
            return str(self) == str(other, 'ascii')
        raise ValueError("'other' has unexpected type {type(other)}")

    def __str__(self):
        if self.special:
            if self.value.startswith('<'):
                return self.value
            return  '^' + self.value
        return self.value


class Browse:
    def __init__(self, shell, index=None):
        self.shell = shell
        self.browse = True
        if index is None:
            self.index = 0
        else:
            self.index = index

        self.ACTIONS = {
            Key.UP: self.up,
            Key.DOWN: self.down,
            Key.RETURN: self.command,
            Key.PGUP: lambda: self.up(step=config.config['General'].getint('page-key-step')),
            Key.PGDN: lambda: self.down(step=config.config['General'].getint('page-key-step')),
            ':': self.command,
        }

    def up(self, step=1):
        self.index -= step

        if self.index < 0:
            self.index = 0

        if self.index - self.shell.offset < 0:
            self.shell.offset += self.index - self.shell.offset


    def down(self, step=1):
        self.index += step

        if self.index > len(self.shell.bib_inds)-1:
            self.index = len(self.shell.bib_inds)-1

        y, x = self.shell.bib_window.getmaxyx()
        limit = y - 2
        if self.index - self.shell.offset >= limit:
            self.shell.offset += self.index - self.shell.offset - limit + 1


    def command(self):
        self.browse = False

    def key_handler(self, key):
        strkey = str(key)
        self.browse = True

        if strkey in self.ACTIONS:
            action = self.ACTIONS[strkey]
            action()

    def run(self):
        self.browse = True
        while self.browse:
            key = Key.read(self.shell.bib_window)
            self.key_handler(key)
            self.shell.draw_bib(self.index)
            self.shell.draw_display(self.index)
        # assert 0, key


class Edit:

    def __init__(self, win, history, start_ch, color):
        self.history = history
        self.win = win
        self.history_id = 0
        self.color = color
        self.start_ch = start_ch
        self.execute = False

        self.ACTIONS = {
            Key.UP: self.load_hist_prev,
            Key.DOWN: self.load_hist_next,
            Key.LEFT: self.prev,
            Key.RIGHT: self.next,
            Key.DELETE: self.delete,
            Key.BACKSPACE: self.back,
            Key.RETURN: self.exit,
            Key.HOME: self.home,
            Key.END: self.end,
            Key.ESCAPE: self.escape,
        }

    def load_history(self):
        hist_len = len(self.history) + 1
        self.history_id = (self.history_id + hist_len) % hist_len
        y, x = self.win.getmaxyx()
        self.win.addstr(1, self.start_ch, ' '*(x - self.start_ch), self.color)

        if self.history_id > 0:
            self.win.addstr(1,self.start_ch,self.history[self.history_id-1], self.color)
        else:
            self.win.move(1,self.start_ch)

    def load_hist_prev(self):
        self.history_id += 1
        self.load_history()

    def load_hist_next(self):
        self.history_id -= 1
        self.load_history()

    def delete(self):
        self.win.delch()

    def prev(self):
        if self.x > self.start_ch:
            self.win.move(self.y, self.x-1)

    def next(self):
        if self.x < self.cols:
            self.win.move(self.y, self.x+1)

    def home(self):
        self.win.move(self.y, 0)

    def end(self):
        self.win.move(self.y, self.cols)

    def back(self):
        if self.x > self.start_ch:
            self.win.move(self.y, self.x-1)
            self.win.delch()

    def exit(self):
        self.edit = False
        self.execute = True

    def escape(self):
        self.edit = False
        self.execute = False

    def content(self):
        line = self.win.instr(1,self.start_ch, curses.COLS - self.start_ch - 1).decode(encoding="utf-8")
        return line

    def key_handler(self, key):
        max_y, max_x = self.win.getmaxyx()
        self.lines = max_y
        self.cols = max_x
        y, x = self.win.getyx()
        self.y = y
        self.x = x

        strkey = str(key)
        self.edit = True

        ret = None

        if strkey in self.ACTIONS:
            action = self.ACTIONS[strkey]
            action()
        elif not key.special:
            self.win.addstr(y, x, strkey, self.color)
            self.win.move(y, x+1)


    def run(self):
        self.edit = True
        curses_edit()
        self.win.move(1,self.start_ch)
        while self.edit:
            self.key_handler(Key.read(self.win))
            self.win.refresh()
        return self.execute



class Shell:

    def __init__(self):
        self.bib_browse = Browse(self)
        self.setup()


    def color(self, key):
        if key not in self._col_inds:
            raise ValueError(f'Color key "{key}" does not exist')
        return curses.color_pair(self._col_inds[key])


    def list_bib(self, limit):
        if len(self.bib_inds) > limit:
            display_bibtex = self.bib_inds[self.offset:(self.offset+limit)]
        else:
            display_bibtex = self.bib_inds

        strs_ = [None]*len(display_bibtex)
        for id_, cid_ in enumerate(display_bibtex):
            entry = self.bibtex.entries[cid_]
            file_ = '   '
            for f in self.docs:
                if f.stem == entry["ID"]:
                    file_ = 'pdf'

            strs_[id_] = f'{cid_:<4}[{file_}]: {entry["ID"]}'
        return strs_


    def draw_bib(self, bib_id=None):
        self.bib_window.erase()
        self.bib_window.bkgd(' ', self.color('background'))
        
        y, x = self.bib_window.getmaxyx()
        limit = y - 2

        lines = self.list_bib(limit)
        self.screen.addnstr(0, 1, self.search, self.bib_w-1, self.color('search'))
        self.screen.noutrefresh()

        for i in range(len(lines)):
            attrs = self.color('bib-line')
            if bib_id is not None:
                if bib_id - self.offset == i:
                    attrs = self.color('bib-line-select')

            self.bib_window.addnstr(i+1, 1, lines[i], self.bib_w-2, attrs)
        
        self.bib_window.border()
        self.bib_window.refresh()


    def draw_display(self, bib_id=None):
        self.display_window.erase()
        self.display_window.bkgd(' ', self.color('background'))
        y, x = self.display_window.getmaxyx()

        if bib_id is None:
            return

        entryid = self.bib_inds[bib_id]
        entry = self.bibtex.entries[entryid]
        row = 0
        for i, key_ in enumerate(entry):
            row += 1
            key = key_ + ': '
            if row > y-1:
                break
            self.display_window.addnstr(row, 1, key, x-2, self.color('bib-key'))
            max_len = x-2-len(key)
            entry_str = str(entry[key_])

            if len(entry_str) <= max_len:
                self.display_window.addstr(row, 1+len(key), entry_str, self.color('bib-item'))
            else:
                words = entry_str.split(' ')
                wid = 0
                item = ''
                for wid, word in enumerate(words):
                    if len(word) > max_len:
                        item += word[:(max_len - len(item) - 1)] + '-'
                        self.display_window.addstr(row, 1+len(key), item, self.color('bib-item'))
                        row += 1
                        item = word[(max_len - len(item) - 1):] + ' '
                    else:
                        if len(item) + len(word) + 1 > max_len:
                            self.display_window.addstr(row, 1+len(key), item, self.color('bib-item'))
                            row += 1
                            if row > y-1:
                                break
                            item = ''
                        item += word + ' '
                if row > y-1:
                    break
                self.display_window.addstr(row, 1+len(key), item, self.color('bib-item'))

        self.display_window.border()
        self.display_window.refresh()


    def draw_cmd(self):
        self.cmdwin.bkgd(' ', self.color('background'))

        self.cmdwin.addstr(1,1,' '*len(self.prompt), self.color('prompt'))
        
        y, x = self.cmdwin.getmaxyx()
        start_ch = 1 + len(self.prompt)
        self.cmdwin.addstr(1, start_ch, ' '*(x - start_ch - 1), self.color('command'))
        
        self.cmdwin.border()
        self.cmdwin.refresh()


    def do_quit(self, args=None):
        return True


    def restore_curses(self):
        curses.nocbreak()
        self.screen.keypad(False)
        curses.endwin()


    def process(self, cmd):
        #todo: do more command processing to extract variables
        split_cmd = cmd.split(' ')
        func_name = 'do_' + split_cmd[0].strip()
        if len(split_cmd) > 1:
            params = ' '.join(split_cmd[1:])
        else:
            params = ''

        self.precmd(cmd)

        if hasattr(self, func_name):
            func = getattr(self, func_name)
            stop = func(params)
        else:
            self.output = f"Don't understand '{cmd}'"
            stop = False

        self.postcmd(stop, cmd)
        return stop

    def precmd(self, cmd):
        pass

    def postcmd(self, stop, cmd):
        self.cmd_history += [cmd]

        self.screen.addnstr(0, self.bib_w, ' '*(self.display_w-1), self.display_w-1, self.color('search'))
        self.screen.addnstr(0, self.bib_w, self.output, self.display_w-1, self.color('search'))

        self.cmdwin.noutrefresh()
        self.screen.noutrefresh()
        curses.doupdate()


    def setup_colors(self):
        self._col_inds = dict()
        for ind, key in enumerate(config.colors):
            self._col_inds[key] = ind+1
            curses.init_pair(ind+1, *config.colors[key].pair())
    

    def do_load(self, args=None):
        '''Load bibtex file and list of papers'''
        self.bibtex = bib.load_bibtex(config.BIB_FILE)
        self.bib_inds = list(range(len(self.bibtex.entries)))
        self.docs = glob(str(config.PAPERS_FOLDER / '*.pdf'))
        self.docs = [pathlib.Path(p) for p in self.docs]




    def setup(self):
        self.bibtex = None
        self.docs = None
        self.current_docs = None
        self.current_bibtex = None

        self.prompt = ': '
        self.offset = 0

        self.cmd_history = []
        self.search = '(No search applied)'

        self.use_colors = config.config['General'].getboolean('use colors')

        self.screen = curses.initscr()
        curses.noecho()

        self.cmdbox_h = 3
        self.search_h = 1
        self.output_h = 1

        if curses.has_colors() and self.use_colors:
            curses.start_color()
            self.setup_colors()

        curses_ui()


        self.screen.bkgd(' ', self.color('background'))
        self.screen.noutrefresh()

        self.bib_h = curses.LINES - self.cmdbox_h - self.search_h
        self.bib_w = int(curses.COLS*config.config['General'].getfloat('split-size'))
        self.bib_window = curses.newwin(self.bib_h, self.bib_w, self.search_h, 0)
        self.bib_window.keypad(True)

        self.display_h = curses.LINES - self.cmdbox_h - self.output_h
        self.display_w = curses.COLS - self.bib_w
        self.display_window = curses.newwin(self.display_h, self.display_w, self.output_h, self.bib_w)
        self.display_window.keypad(True)

        self.cmdwin = curses.newwin(self.cmdbox_h, curses.COLS, self.bib_h + self.search_h, 0)
        self.cmdwin.keypad(True)

        self.do_load()
        if len(self.bibtex.entries) > 0:
            bid = 0
        else:
            bid = None
        self.draw_bib(bid)
        self.draw_display(bid)
        self.draw_cmd()

        curses.doupdate()



    def get_command(self):

        self.cmdwin.addstr(1,1,self.prompt, self.color('prompt'))
        curses_edit()
        cmd_enter = Edit(self.cmdwin, self.cmd_history, len(self.prompt) + 1, self.color('command'))
        execute = cmd_enter.run()
        curses_ui()
        if execute:
            cmd = cmd_enter.content().strip()
            self.draw_cmd()
        else:
            cmd = ''
        self.cmdwin.addstr(1,1,' '*len(self.prompt), self.color('prompt'))
        return cmd



def run():
    prompt = Shell()
    stop = False

    try:
        while not stop:

            prompt.bib_browse.run()

            text = prompt.get_command()
            if len(text) > 0:
                stop = prompt.process(text)

    except (Exception, KeyboardInterrupt) as excep:
        prompt.restore_curses()
        raise excep
    prompt.restore_curses()




