import sys
import pathlib
import configparser

try:
    # PyXDG
    # https://www.freedesktop.org/wiki/Software/pyxdg/
    from xdg import BaseDirectory
except ImportError:
    BaseDirectory = None


class Terminal:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    BULLET = '\u2022'

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
    with open(CONF_FILE, 'w') as configfile:
        config.write(configfile)

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
