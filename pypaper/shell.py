
#Python standard
from glob import glob
import os
import pathlib
import subprocess
import re
import string
import curses
import curses.textpad

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
    pass


class Edit:

    def __init__(self, win, history, start_ch, color):
        self.history = history
        self.win = win
        self.history_id = 0
        self.color = color
        self.start_ch = start_ch

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
        }

    def load_history(self):
        hist_len = len(self.history) + 1
        self.history_id = (self.history_id + hist_len) % hist_len
        y, x = self.win.getmaxyx()
        self.win.addstr(0, self.start_ch, ' '*(x - self.start_ch), self.color)

        if self.history_id > 0:
            self.win.addstr(0,self.start_ch,self.history[self.history_id], self.color)
        self.win.noutrefresh()

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

    def content(self):
        line = self.win.instr(0,self.start_ch, curses.COLS - self.start_ch - 1).decode(encoding="utf-8")
        return line.strip()

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
            self.win.addstr(y,x,strkey, self.color)
            self.win.move(y, x+1)


    def run(self):
        self.edit = True
        self.win.move(0,self.start_ch)
        while self.edit:
            self.key_handler(Key.read(self.win))



class Shell:

    def __init__(self):
        self.setup()


    def color(self, key):
        if key not in self._col_inds:
            raise ValueError(f'Color key "{key}" does not exist')
        return curses.color_pair(self._col_inds[key])


    def draw_bib(self):
        self.bib_window.clear()

        lines = self.list_bib()

        if len(lines) >= self.bib_h:
            lines = lines[-self.bib_h:]

        for i in range(len(lines)):
            self.bib_window.addnstr(i, 1, lines[i], self.bib_w-2, self.color('bib-line'))
        
        self.bib_window.border()
        self.bib_window.noutrefresh()


    def draw_display(self):
        self.display_window.clear()

        self.display_window.border()
        self.display_window.noutrefresh()



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

        if hasattr(self, func_name):
            func = getattr(self, func_name)
        else:
            func = self.default

        self.precmd(cmd)
        stop = func(params)
        self.postcmd(stop, cmd)
        return stop

    def precmd(self, cmd):
        pass

    def postcmd(self, stop, cmd):
        self.cmd_history += [cmd]
        self.cmdwin.noutrefresh()
        self.screen.noutrefresh()
        curses.doupdate()


    def setup_colors(self):
        self._col_inds = dict()
        for ind, key in enumerate(config.colors):
            self._col_inds[key] = ind
            curses.init_pair(ind, *config.colors[key].pair())
    

    def do_load(self, args=None):
        '''Load bibtex file and list of papers'''
        self.bibtex = bib.load_bibtex(config.BIB_FILE)
        self.bib_inds = []
        self.docs = glob(str(config.PAPERS_FOLDER / '*.pdf'))
        self.docs = [pathlib.Path(p) for p in self.docs]


    def list_bib(self):
        if len(self.bib_inds) == 0:
            if len(self.bibtex.entries) > self.limit:
                display_bibtex = list(range(self.limit))
            else:
                display_bibtex = list(range(len(self.bibtex.entries)))
        else:
            if len(self.bib_inds) > self.limit:
                display_bibtex = self.bib_inds[:self.limit]
            else:
                display_bibtex = self.bib_inds

        strs_ = [None]*len(display_bibtex)
        for id_, cid_ in enumerate(display_bibtex):
            entry = self.bibtex.entries[cid_]
            file_ = '   '
            for f in self.docs:
                if f.stem == entry["ID"]:
                    file_ = 'pdf'

            strs_[id_] = f'{id_:<4}[{file_}]: {entry["ID"]}'
        return strs_



    def setup(self):
        self.bibtex = None
        self.docs = None
        self.current_docs = None
        self.current_bibtex = None
        self.limit = 20

        self.prompt = ': '

        self.cmd_history = []
        self.selection = ''

        self.use_colors = True

        self.screen = curses.initscr()
        curses.noecho()
        self.screen.keypad(True)

        self.cmdbox_h = 1
        self.search_h = 1
        self.output_h = 4

        if curses.has_colors() and self.use_colors:
            curses.start_color()
            curses.use_default_colors()
            self.setup_colors()

        try:
            curses.curs_set(1)
        except:
            pass

        self.screen.attrset(self.color('background'))
        # self.screen.bkgd(' ', self.color('background'))
        # self.screen.bkgdset(' ', self.color('background'))
        self.screen.noutrefresh()

        self.bib_h = curses.LINES - self.cmdbox_h - self.search_h - 1
        self.bib_w = curses.COLS//2
        self.bib_window = curses.newwin(self.bib_h, self.bib_w, self.search_h, 0)
        self.bib_window.bkgd(' ', self.color('background'))
        
        
        self.display_h = curses.LINES - self.cmdbox_h - 1
        self.display_w = curses.COLS//2
        self.display_window = curses.newwin(self.display_h, self.display_w, 0, self.bib_w)
        self.display_window.bkgd(' ', self.color('background'))

        self.cmdwin = curses.newwin(self.cmdbox_h, curses.COLS, curses.COLS - self.cmdbox_h - 1, 0)
        self.cmdwin.bkgd(' ', self.color('background'))
        self.cmdwin.border()
        self.cmdwin.addstr(0,1,self.prompt, self.color('prompt'))
        self.cmdwin.addstr(0,1 + len(self.prompt),' '*(curses.COLS - 2 - len(self.prompt)), self.color('command'))
        self.cmdwin.noutrefresh()

        self.do_load()

        self.draw_bib()
        self.draw_display()

        curses.doupdate()


    def get_command(self):
        self.cmdwin.refresh()

        cmd_enter = Edit(self.cmdwin, self.cmd_history, len(self.prompt) + 1, self.color('command'))
        cmd_enter.run()
        cmd = cmd_enter.content().strip()
        return cmd
        

    def default(self, cmd=None):
        self.write("Don't understand '" + cmd + "'", clear=True)


    def write(self, line, clear=False):
        if clear:
            self.output = ''
        self.output += '\n' + line



def run():
    prompt = Shell()
    stop = False

    try:
        while not stop:
            text = prompt.get_command()
            # assert 0, text
            stop = prompt.process(text)

    except (Exception, KeyboardInterrupt) as excep:
        prompt.restore_curses()
        raise excep
    prompt.restore_curses()




