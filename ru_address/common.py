import glob
import os
import re
import time
import psutil


class Common:
    """Utils"""
    @staticmethod
    def build_ngrams(keyword, n=3, filler="__"):
        keyword_w_filler = filler + keyword + filler
        left_length = len(keyword_w_filler) - len(filler)

        trigrams = []
        for i in range(0, left_length):
            trigrams.append(keyword_w_filler[i:i + n])

        return " ".join(trigrams)

    @staticmethod
    def clear_keyword(keyword, regex=re.compile(r"[\s\"'.,()\-_\\\/]")):
        keyword = regex.sub("_", keyword)
        return keyword.lower()

    @staticmethod
    def update_progress(progress):
        # Отображает отформатированный прогресс-бар
        print("\r[{0:50s}] {1:.1f}% ".format('#' * int(progress * 50), progress * 100), end="", flush=True)

    @staticmethod
    def cli_output(message):
        now = time.strftime("%H:%M:%S")
        print(f'[{now}] {message}')

    @staticmethod
    def show_memory_usage():
        process = psutil.Process(os.getpid())
        print(f'> Memory usage: {round(process.memory_info().rss / 1024 / 1024, 2)}M')

    @staticmethod
    def show_execution_time(start_time):
        time_measure = time.time() - start_time
        print(f"> Execution time: {round(time_measure, 2)}s")

    @staticmethod
    def get_source_filepath(source_path, table, extension):
        """ Ищем файл таблицы в папке с исходниками,
        Названия файлов в непонятном формате, например AS_ACTSTAT_2_250_08_04_01_01.xsd"""
        file = f'AS_{table}_2*.{extension}'
        file_path = os.path.join(source_path, file)
        found_files = glob.glob(file_path)
        if len(found_files) == 1:
            return found_files[0]
        if len(found_files) > 1:
            raise FileNotFoundError(f'More than one file found: {file_path}')
        raise FileNotFoundError(f'Not found source file: {file_path}')


class DataSource:
    def __init__(self, filename):
        self.size = os.path.getsize(filename)
        self.delivered = 0
        self.f = open(filename, 'r', encoding='utf-8')

    def read(self, size=None):
        if size is None:
            self.delivered = self.size
            return self.f.read()

        data = self.f.read(size)
        self.delivered += len(data)
        return data

    def close(self):
        self.f.close()

    @property
    def percentage(self):
        return float(self.delivered) / self.size * 100.0


class TableRepresentation:
    """ Набор параметров для презентации табличных данных в виде текстового файла """
    def __init__(self, quotes="\"", quotes_system="`", delimiter=", ", row_indent="\t", row_parentheses=("(", ")"),
                 line_ending=',\n', line_ending_last=';\n', bool_repr=('0', '1'), null_repr="NULL",
                 table_start_handler=None, table_end_handler=None,  batch_start_handler=None):
        self.quotes = quotes
        self.quotes_system = quotes_system
        self.delimiter = delimiter
        self.row_indent = row_indent
        self.row_parentheses = row_parentheses
        self.line_ending = line_ending
        self.line_ending_last = line_ending_last
        self.bool_repr = bool_repr
        self.null_repr = null_repr
        self.table_start_handler = table_start_handler
        self.table_end_handler = table_end_handler
        self.batch_start_handler = batch_start_handler

