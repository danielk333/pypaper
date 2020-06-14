
#Python standard
from cmd import Cmd
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


class Color:

    def __init__(self, fg, bg=None):
        self.fg = fg
        self.bg = bg

    def pair(self):
        return [self.fg, self.bg]

    def __eq__(self, other):
        return self.fg == other.fg and self.bg == other.bg




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


class Edit:

    def __init__(self, win, history):
        self.history = history
        self.win = win
        self.history_id = 0

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
        self.win.clear()
        if self.history_id > 0:
            self.win.addstr(0,0,self.history[self.history_id])
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
        if self.x > 0:
            self.win.move(self.y, self.x-1)

    def next(self):
        if self.x < self.cols:
            self.win.move(self.y, self.x+1)

    def home(self):
        self.win.move(self.y, 0)

    def end(self):
        self.win.move(self.y, self.cols)

    def back(self):
        if self.x > 0:
            self.win.move(self.y, self.x-1)
            self.win.delch()

    def exit(self):
        self.edit = False

    def content(self):
        line = self.win.instr(0,0).decode(encoding="utf-8")
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
            self.win.addstr(y,x,strkey)
            self.win.move(y, x+1)


    def run(self):
        self.edit = True
        while self.edit:
            self.key_handler(Key.read(self.win))



class Shell(Cmd):

    def color(self, ind=1):
        return curses.color_pair(ind)


    def draw_terminal(self):
        self.terminal_window.clear()

        if len(self.terminal_lines) >= self.terminal_h:
            self.terminal_lines = self.terminal_lines[-self.terminal_h:]

        self.terminal_window.hline(self.terminal_h-1,0,curses.ACS_HLINE,self.terminal_w,0)
        j = 1
        for i in range(len(self.terminal_lines)-1,-1,-1):
            self.screen.addstr(self.terminal_h - j, 0, self.terminal_lines[i])
            j += 1
        self.screen.noutrefresh()


    def draw_display(self):
        pass


    def do_quit(self, line):
        #self.do_save('')
        return True


    def restore_curses(self):
        curses.nocbreak()
        self.screen.keypad(False)
        curses.endwin()


    def precmd(self, line):
        self.terminal_lines += [self.prompt + line]


    def postcmd(self, stop, line):
        self.cmd_history += [line]
        self.cmdwin.clear()
        self.cmdwin.noutrefresh()
        self.screen.noutrefresh()
        self.draw_terminal()
        self.draw_display()
        curses.doupdate()


    def setup_colors(self):
        curses.init_pair(1, *(7, 0))
        curses.init_pair(2, *(8, 0))
        

    def setup(self):
        self.bibtex = None
        self.docs = None
        self.current_docs = None
        self.current_bibtex = None
        self.limit = 20

        self.terminal_lines = []
        self.cmd_history = []

        self.use_colors = True

        self.screen = curses.initscr()
        curses.noecho()
        self.screen.keypad(True)

        self.cmdbox_h = 1

        if curses.has_colors() and self.use_colors:
            curses.start_color()
            curses.use_default_colors()
            self.setup_colors()

        try:
            curses.curs_set(1)
        except:
            pass

        self.screen.attrset(self.color())
        self.screen.noutrefresh()

        self.terminal_h = curses.LINES - self.cmdbox_h - 1
        self.terminal_w = curses.COLS//2
        self.terminal_window = curses.newwin(self.terminal_h, self.terminal_w, 0, 0)
        self.terminal_window.bkgd(' ', self.color())
        self.terminal_window.noutrefresh()
        
        self.display_h = curses.LINES
        self.display_w = curses.COLS//2
        self.display_window = curses.newwin(self.display_h, self.display_w, 0, self.terminal_w)
        self.display_window.border()
        self.display_window.bkgd(' ', self.color())
        self.display_window.noutrefresh()

        self.cmdwin = curses.newwin(self.cmdbox_h, self.terminal_w, self.terminal_h, 0)
        self.display_window.bkgd(' ', self.color(2))
        self.display_window.noutrefresh()

        self.draw_terminal()
        self.draw_display()

        curses.doupdate()


    def get_command(self):
        self.cmdwin.clear()
        self.cmdwin.refresh()
        
        cmd_enter = Edit(self.cmdwin, self.cmd_history)
        cmd_enter.run()
        return cmd_enter.content()
        


    def default(self,line):
        self.write("Don't understand '" + line + "'")


    def write(self, line):
        self.terminal_lines += [line]



def run():
    prompt = Shell()
    flag = False

    try:
        prompt.prompt = '> '
        prompt.setup()
        while not flag:
            text = prompt.get_command()

            prompt.precmd(text)
            flag = prompt.onecmd(text)
            prompt.postcmd(flag, text)

    except (Exception, KeyboardInterrupt) as excep:
        prompt.restore_curses()
        raise excep
    prompt.restore_curses()




