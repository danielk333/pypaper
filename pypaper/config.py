import sys
import pathlib
import configparser
import curses

try:
    # PyXDG
    # https://www.freedesktop.org/wiki/Software/pyxdg/
    from xdg import BaseDirectory
except ImportError:
    BaseDirectory = None


config = configparser.ConfigParser()

HOME = pathlib.Path.home()
CONF_FOLDER = HOME / '.config'
CONF_FILENAME = 'pypaper.conf'
CONF_FILE = None

if BaseDirectory is not None:
    CONF_FOLDER = pathlib.Path(BaseDirectory.xdg_config_home)
    CONF_FILE = pathlib.Path(BaseDirectory.load_first_config(CONF_FILENAME))

if CONF_FILE is None:
    CONF_FILE = CONF_FOLDER / CONF_FILENAME

CONF_FILE.parent.mkdir(parents=True, exist_ok=True)


DEFAULT = {
    'General': {
        'path': str(HOME / 'pypapers'),
        'viewer': 'okular',
        'title include': 0,
        'use colors': True,
        'split-size': 0.7,
        'page-key-step': 10,
        'format': '{index:<4} {pdf} [{year}] {author}: {title}',
    },
    'Color': {
        'background': 7,
        'select-background': 8,
        'text': 0,
        'command': 4,
        'prompt': 1,
        'search': 1,
        'output': 4,
        'bib-line': 0,
        'bib-line-select': 0,
        'bib-key': 1,
        'bib-item': 0,
    },
    'ADS': {
        'token': 'place your personal token here',
        'max results': 20,
    },
}

config.read_dict(DEFAULT)

if CONF_FILE.exists():
    config.read([CONF_FILE])
else:
    configfile.touch()

DATA_FOLDER = pathlib.Path(config['General']['path'])

PICKUP_FOLDER = DATA_FOLDER / 'PICKUP'
BIB_FILE = DATA_FOLDER / 'references.bib'
PAPERS_FOLDER = DATA_FOLDER / 'PAPERS'
TRASH_FOLDER = DATA_FOLDER / 'TRASH'

DATA_FOLDER.mkdir(parents=True, exist_ok=True)

if not BIB_FILE.exists():
    BIB_FILE.touch()

DATA_FOLDER.mkdir(parents=True, exist_ok=True)
PICKUP_FOLDER.mkdir(exist_ok=True)
PAPERS_FOLDER.mkdir(exist_ok=True)
TRASH_FOLDER.mkdir(exist_ok=True)


class Color:

    def __init__(self, fg, bg=None):
        self.fg = fg
        self.bg = bg

    def pair(self):
        return [self.fg, self.bg]

    def __eq__(self, other):
        return self.fg == other.fg and self.bg == other.bg

if config['General'].getboolean('use colors'):
    colors = {
        'standard': Color(config['Color'].getint('text'), config['Color'].getint('background')),
    }
    for key in config['Color']:
        if key not in ['text', 'background', 'select-background']:
            if key.split('-')[-1] == 'select':
                colors[key] = Color(config['Color'].getint(key), config['Color'].getint('select-background'))
            else:
                colors[key] = Color(config['Color'].getint(key), config['Color'].getint('background'))

else:
    colors = None