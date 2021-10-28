from Filepaths import DATA_FOLDER
import pathlib
import shutil
import gzip
import os


class LogObserver:
    def __init__(self, log_Path: pathlib.Path):
        self.__log_path = log_Path  # P is capitalized to indicate Path object
        self.__copy_path = DATA_FOLDER / f'Copy of {log_Path.name}'  # todo remove previous logs?
        self.__last_modified = 0
        self.__jump_point = 0

    def get_log_path(self):
        return self.__log_path

    def read_new_lines(self, from_char=None, limit=None):
        mod_time = os.path.getmtime(self.__log_path)
        if mod_time <= self.__last_modified:
            # there will only be new lines if the file has been modified since the last read
            return []
        if not limit:  # only update the last modified time if all available lines have been read
            self.__last_modified = mod_time

        shutil.copy(self.__log_path, self.__copy_path)
        new_lines = []
        with gzip.open(self.__copy_path, 'rt') as file:
            file.seek(from_char if from_char is not None else self.__jump_point)
            while not limit or len(new_lines) < limit:
                try:
                    line = file.readline()
                    if not line:
                        break
                    new_lines.append(line.strip())
                except EOFError as e:
                    print(e)
                    break
            else:
                print('log completed (?)')

        self.__jump_point += sum(len(line) for line in new_lines)
        return new_lines

    def __str__(self):
        return f'Observer of {self.__log_path}: [{self.__jump_point} characters read]'
