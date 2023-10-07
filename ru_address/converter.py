import os
import glob
import datetime

from ru_address.source.xml import Definition
from ru_address.source.xml import Data
from ru_address._version import __version__


class Converter:
    SOURCE_XML = 'xml'

    TABLE_LIST = [
        'ACTSTAT',
        'ADDROBJ',
        'CENTERST',
        'CURENTST',
        'ESTSTAT',
        'FLATTYPE',
        'HOUSE',
        'NDOCTYPE',
        'NORMDOC',
        'OPERSTAT',
        'ROOMTYPE',
        'ROOM',
        'SOCRBASE',
        'STEAD',
        'STRSTAT'
    ]

    def __init__(self, source, source_path, beta):
        self.source = source
        self.source_path = source_path
        self.beta = beta

    def get_source_filepath(self, table, extension):
        """ Ищем файл таблицы в папке с исходниками,
        Названия файлов в непонятном формате, например AS_ACTSTAT_2_250_08_04_01_01.xsd"""
        file = f'AS_{table}_*.{extension}'
        file_path = os.path.join(self.source_path, file)
        found_files = glob.glob(file_path)
        if len(found_files) == 1:
            return found_files[0]
        elif len(found_files) > 1:
            raise FileNotFoundError(f'More than one file found: {file_path}')
        else:
            raise FileNotFoundError(f'Not found source file: {file_path}')

    def convert_table(self, file, table, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и XML файлы. """
        if self.source == self.SOURCE_XML:
            self._convert_table_xml(file, table, skip_definition, skip_data, batch_size)

    def _convert_table_xml(self, file, table, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и XML файлы. """
        dump_file = file

        source_filepath = self.get_source_filepath(table, 'xsd')
        definition = Definition(table, source_filepath)
        if skip_definition is False:
            definition.convert_and_dump(dump_file)

        if skip_data is False:
            source_filepath = self.get_source_filepath(table, 'xml')
            data = Data(table, source_filepath)
            if self.beta:
                data.convert_and_dump_v2(dump_file, definition, batch_size)
            else:
                data.convert_and_dump(dump_file, definition, batch_size)

    @staticmethod
    def prepare_table_input(table_list_string):
        """ Подготавливает переданный через аргумент список таблиц """
        table_list = table_list_string.split(',')
        for table in table_list:
            if table not in Converter.TABLE_LIST:
                raise ValueError(f'Unknown table "{table}"')
        return table_list

    @staticmethod
    def get_dump_copyright():
        """ Сообщение в заголовок сгенерированного файла """
        header = ("-- --------------------------------------------------------\n"
                  "-- ver. {}\n"
                  "-- get latest version @ https://github.com/shadz3rg/ru_address\n"
                  "-- file generated {}\n"
                  "-- --------------------------------------------------------\n\n")
        now = datetime.datetime.now()
        return header.format(__version__, str(now))

    @staticmethod
    def get_dump_header(encoding):
        """ Подготовка к импорту """
        header = ("/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;\n"
                  "/*!40101 SET NAMES {} */;\n"
                  "/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;\n"
                  "/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;\n")
        return header.format(encoding)

    @staticmethod
    def get_dump_footer():
        """ Завершение импорта """
        footer = ("\n/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;\n"
                  "/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;\n"
                  "/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;")
        return footer

    @staticmethod
    def get_table_separator(table):
        return f"\n\n-- Table `{table}`\n"

class Output:
    """Conversion result helper"""
    SINGLE_FILE = 0
    FILE_PER_TABLE = 1

    def __init__(self, output_path, mode):
        self.output_path = output_path
        self.mode = mode

    def get_table_filename(self, table):
        return f'{table}.sql'

    def open_dump_file(self, filename):
        filepath = os.path.join(self.output_path, filename)
        return open(filepath, 'w', encoding='utf-8')
