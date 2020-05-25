import sys
import pathlib
import configparser
import os

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

HOME = pathlib.Path(os.path.expanduser("~"))
CONF_FOLDER = HOME / '.config'
CONF_FILE = CONF_FOLDER / 'pypaper.conf'

CONF_FOLDER.mkdir(parents=True, exist_ok=True)


DEFAULT = {
    'General': {
        'path': str(HOME / 'pypapers'),
        'viewer': 'okular',
        'title include': 0,
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

if not BIB_FILE.exists():
  BIB_FILE.touch()

DATA_FOLDER.mkdir(parents=True, exist_ok=True)
PICKUP_FOLDER.mkdir(exist_ok=True)
PAPERS_FOLDER.mkdir(exist_ok=True)
TRASH_FOLDER.mkdir(exist_ok=True)