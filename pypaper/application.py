#Python standard
import os
import pathlib
import re
import string
import curses



def curs_set(show=True):
    if show:
        setn = 1
    else:
        setn = 0

    try:
        curses.curs_set(setn)
    except:
        pass

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
    RESIZE = '<resize>'

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
        elif value == curses.KEY_RESIZE:
            return Key(Key.RESIZE, True)
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


class State:

    def __init__(self, window, curs_show=False):
        self.curs_show = curs_show
        self.window = window
        self.actions = {
            '^C': self.interrupt,
        }
        self.data = None

    def interrupt(self):
        self.data = 'exit'
        return False

    def draw(self):
        raise NotImplementedError('')


    def default(self, key):
        raise NotImplementedError('')


    def key_handler(self, key):
        strkey = str(key)

        if strkey in self.actions:
            action = self.actions[strkey]
            ret = action()
        else:
            ret = self.default(key)

        if ret is None:
            ret = True
        return ret


    def run(self):
        self.data = None
        curs_set(show=self.curs_show)
        enabled = True
        while enabled:
            key = Key.read(self.window)
            enabled = self.key_handler(key)
            self.draw()
        return self.data


class UnseenFormatter(string.Formatter):
    def get_value(self, key, args, kwds):
        if isinstance(key, str):
            try:
                return kwds[key]
            except KeyError:
                return key
        else:
            return string.Formatter.get_value(key, args, kwds)


class Browse(State):
    def __init__(self, window, lst, fmt, color, select_color, pg_step = 10, margin = 1, border=True):
        super().__init__(window, curs_show=False)

        self.lst = lst
        self.subset = None
        self.fmt = fmt

        self.formatter = UnseenFormatter()

        self.color = color
        self.select_color = select_color
        self.border = border

        self.pg_step = pg_step
        self.offset = 0
        self.index = 0
        self.margin = margin

        self.actions.update({
            Key.UP: self.up,
            Key.DOWN: self.down,
            Key.RETURN: self.exit,
            Key.PGUP: lambda: self.up(step=self.pg_step),
            Key.PGDN: lambda: self.down(step=self.pg_step),
        })


    @property
    def limit(self):
        y, x = self.window.getmaxyx()
        return y - 2*self.margin, x - 2*self.margin


    def default(self, key):
        pass


    def up(self, step=1):
        self.index -= step
        if self.index < 0:
            self.index = 0
        if self.index - self.offset < 0:
            self.offset += self.index - self.offset


    def down(self, step=1):
        self.index += step
        if self.index > len(self.subset)-1:
            self.index = len(self.subset)-1
        limit, _ = self.limit
        if self.index - self.offset >= limit:
            self.offset += self.index - self.offset - limit + 1


    def exit(self):
        return False


    def draw(self):
        self.window.erase()
        self.window.bkgd(' ', self.color)
        
        limit, fmt_len = self.limit

        draw_set = self.subset[self.offset:(self.offset+limit)]

        for i in range(len(draw_set)):
            if self.index - self.offset == i:
                attrs = self.select_color
            else:
                attrs = self.color

            line = self.formatter.format(self.fmt, index=i+self.offset, row=i, id=draw_set[i], **self.lst[draw_set[i]])
            #some cleaning
            line = line.replace('\n', ' ')
            try:
                self.window.addnstr(i+self.margin, self.margin, line, fmt_len, attrs)
            except:
                raise Exception(str((i+self.margin, self.margin, line, fmt_len, attrs)))
        
        if self.border:
            self.window.border()
        self.window.refresh()


    def run(self):
        if self.subset is None:
            self.subset = list(range(len(self.lst)))
        return super().run()



class BrowseDisplay(Browse):
    def __init__(self, window, display_window, lst, fmt, color, select_color, **kwargs):
        super().__init__(window, lst, fmt, color, select_color, **kwargs)
        self.display_window = display_window


    def draw_item(self, item):
        raise NotImplementedError()


    def draw(self):
        super().draw()
        self.display_window.erase()
        self.display_window.bkgd(' ', self.color)
        self.draw_item(self.lst[self.index])
        self.display_window.refresh()





class Shell(State):

    def __init__(self, window, prompt, prompt_color, command_color, border=True, prompt_line = 1):
        super().__init__(window, curs_show=True)
        self.history = []
        self.history_max = None
        self.history_id = 0

        self.prompt_line = prompt_line

        self.prompt = prompt
        self.prompt_color = prompt_color
        self.command_color = command_color

        self.border = border

        self.start_ch = len(self.prompt)

        self.actions.update({
            Key.UP: self.load_hist_prev,
            Key.DOWN: self.load_hist_next,
            Key.LEFT: self.prev,
            Key.RIGHT: self.next,
            Key.DELETE: self.delete,
            Key.BACKSPACE: self.back,
            Key.RETURN: self.execute,
            Key.HOME: self.home,
            Key.END: self.end,
            Key.ESCAPE: self.escape,
        })


    def clear_cmd(self):
        self.window.erase()
        self.window.bkgd(' ', self.command_color)

        y, x = self.window.getmaxyx()
        if self.border:
            self.window.border()

        self.window.addstr(self.prompt_line, 0, ' '*x, self.command_color)
        self.window.addstr(self.prompt_line, 0, self.prompt, self.prompt_color)
        self.window.refresh()


    def enter_command(self, cmd):
        self.clear_cmd()
        y,x = self.window.getmaxyx()
        self.window.addnstr(self.prompt_line, self.start_ch, cmd, y-self.start_ch-1, self.command_color)
        self.draw()


    def draw(self):
        self.window.refresh()


    def load_history(self):
        hist_len = len(self.history) + 1
        self.history_id = (self.history_id + hist_len) % hist_len

        self.clear_cmd()

        if self.history_id > 0:
            self.window.addstr(self.prompt_line,self.start_ch,self.history[self.history_id-1], self.command_color)
            self.window.move(self.prompt_line,self.start_ch + len(self.history[self.history_id-1]))
        else:
            self.window.move(self.prompt_line,self.start_ch)



    def load_hist_prev(self):
        self.history_id += 1
        self.load_history()

    def load_hist_next(self):
        if self.history_id > 0:
            self.history_id -= 1
            self.load_history()

    def delete(self):
        self.window.delch()

    def prev(self):
        _, x = self.window.getyx()
        if x > self.start_ch:
            self.window.move(self.prompt_line, x-1)

    def next(self):
        _, xmax = self.window.getmaxyx()
        _, x = self.window.getyx()
        if x < xmax-1:
            self.window.move(self.prompt_line, x+1)

    def home(self):
        self.window.move(self.prompt_line, self.start_ch)

    def end(self):
        cmd = self.get_command()
        self.window.move(self.prompt_line, self.start_ch + len(cmd) - 1)

    def back(self):
        y, x = self.window.getyx()
        if x > self.start_ch:
            self.window.move(self.prompt_line, x-1)
            self.window.delch()

    def execute(self):
        self.data = self.get_command()
        self.history.insert(0, self.data)
        if self.history_max is not None:
            if len(self.history) > self.history_max:
                self.history = self.history[1:]
        self.clear_cmd()
        return False

    def escape(self):
        self.data = ''
        return False

    def get_command(self):
        y, x = self.window.getmaxyx()
        cmd = self.window.instr(self.prompt_line,self.start_ch, x - self.start_ch - 1).decode(encoding="utf-8")
        return cmd.strip()

    def default(self, key):
        if not key.special:
            y, x = self.window.getyx()
            self.window.addstr(y, x, str(key), self.command_color)
            self.window.move(y, x+1)

    def run(self):
        cmd = self.get_command().strip()
        self.window.move(self.prompt_line, self.start_ch + len(cmd))
        return super().run()



class App:

    def __init__(self, colors, error_state = 'start'):
        self.states = {}
        self._colors = colors
        self.screen = None
        self.output = ''
        self.error_state = error_state

        self.init_curses()


    def setup_colors(self):
        self._col_inds = dict()
        for ind, key in enumerate(self._colors):
            self._col_inds[key] = ind+1
            curses.init_pair(ind+1, *self._colors[key].pair())


    def color(self, key):
        if key not in self._col_inds:
            raise ValueError(f'Color key "{key}" does not exist')
        return curses.color_pair(self._col_inds[key])


    def init_curses(self):
        self.screen = curses.initscr()
        self.LINES, self.COLS = self.screen.getmaxyx()

        curses.noecho()

        self.screen.erase()
        if self._colors is not None and curses.has_colors():
            curses.start_color()
            self.setup_colors()
            self.screen.bkgd(' ', self.color('standard'))
        else:
            self.screen.bkgd(' ')
        self.screen.noutrefresh()


    def restore_curses(self):
        curses.nocbreak()
        curses.endwin()


    def process(self, cmd):
        _cmd = cmd.strip()
        if len(_cmd) == 0:
            return 'start'

        split_cmd = _cmd.find(' ')
        if split_cmd >= 0:
            func_name = 'do_' + _cmd[:split_cmd]
            params = _cmd[split_cmd:].strip()
        else:
            func_name = 'do_' + _cmd
            params = ''

        self.precmd(cmd)

        if hasattr(self, func_name):
            func = getattr(self, func_name)
            state = func(params)
        else:
            self.output = f"Don't understand '{cmd}'"
            state = self.error_state

        self.postcmd(state, cmd)
        return state


    def precmd(self, cmd):
        pass


    def postcmd(self, state, cmd):
        pass


    def draw_init(self):
        for name in self.states:
            self.states[name].draw()
        self.screen.refresh()
        curses.doupdate()


    def run(self, start):
        self.draw_init()
        exit = False
        state = start
        while not exit:
            data = self.states[state].run()
            new_state = self.process(data)
            if new_state is not None:
                state = new_state

            if state == 'start':
                state = start
            elif state == 'exit':
                exit = True
        self.restore_curses()