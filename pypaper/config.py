import sys
import pathlib
import configparser

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

bg_color = 7
text_color = 0

#todo, custom colors
colors = {
    'background': Color(text_color, bg_color),
    'borders': Color(7, bg_color),
    'text': Color(text_color, bg_color),
    'command': Color(text_color, bg_color),
    'prompt': Color(1, bg_color),
    'bib-line': Color(text_color, bg_color),
    'bib-key': Color(1, bg_color),
    'bib-item': Color(text_color, bg_color),
}
