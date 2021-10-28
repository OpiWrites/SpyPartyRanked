import pathlib
import sys
import os


CWD = pathlib.Path(__file__).parent
DATA_FOLDER = CWD / 'data'


KEYWORD_SPYPARTY_DATADIR = 'SPYPARTYDATA'


def get_default_directory_os_independent() -> pathlib.Path:
    if KEYWORD_SPYPARTY_DATADIR in os.environ:
        sp_data_dir = os.environ[KEYWORD_SPYPARTY_DATADIR]
        return pathlib.Path(sp_data_dir)

    home = pathlib.Path.home()
    match sys.platform:
        case 'win32':
            return home / 'AppData/Local/SpyParty'
        case 'linux' | 'linux2' | 'linux3':
            return home / '.local/share'
        case 'darwin':
            return home / 'Library/Application Support'
        case _:
            raise Exception(f'Unsupported Platform: {sys.platform}; try defining ${KEYWORD_SPYPARTY_DATADIR}.')


def main():
    print(get_default_directory_os_independent())


if __name__ == '__main__':
    main()
