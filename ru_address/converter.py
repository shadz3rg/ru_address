import os
import glob
import datetime

from ru_address.source.xml import Definition
from ru_address.source.xml import Data
from ru_address._version import __version__


class Converter:
    SOURCE_XML = 'xml'
    SOURCE_DBF = 'dbf'

    TABLE_LIST = [
        'ACTSTAT',
        'ADDROBJ',
        'CENTERST',
        'CURENTST',
        'ESTSTAT',
        'HOUSEINT',
        'HSTSTAT',
        'INTVSTAT',
        'LANDMARK',
        'NDOCTYPE',
        'NORMDOC',
        'OPERSTAT',
        'SOCRBASE',
        'STRSTAT'
    ]

    def __init__(self, source, source_path, output):
        self.source = source
        self.source_path = source_path
        self.output = output

    def get_source_filepath(self, table, extension):
        """ Ищем файл таблицы в папке с исходниками, 
        Названия файлов в непонятном формате, например AS_ACTSTAT_2_250_08_04_01_01.xsd
        """
        file = 'AS_{}_*.{}'.format(table, extension)
        file_path = os.path.join(self.source_path, file)
        found_files = glob.glob(file_path)
        if len(found_files) == 1:
            return found_files[0]
        elif len(found_files) > 1:
            raise FileNotFoundError('More than one file found: {}'.format(file_path))
        else:
            raise FileNotFoundError('Not found source file: {}'.format(file_path))

    def convert_table(self, table, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и XML файлы. """
        if self.source == self.SOURCE_XML:
            self._convert_table_xml(table, skip_definition, skip_data, batch_size)
        elif self.source == self.SOURCE_DBF:
            self._convert_table_dbf(table, skip_definition, skip_data, batch_size)
            pass

    def _convert_table_xml(self, table, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и XML файлы. """
        dump_file = self.output.open_dump_file(table)
        dump_file.write(Converter.get_dump_header())

        source_filepath = self.get_source_filepath(table, 'xsd')
        definition = Definition(table, source_filepath)
        if skip_definition is False:
            definition.convert_and_dump(dump_file)

        if skip_data is False:
            source_filepath = self.get_source_filepath(table, 'xml')
            data = Data(table, source_filepath)
            data.convert_and_dump(dump_file, definition.get_table_fields(), batch_size)

    def _convert_table_dbf(self, table, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и DBF файлы. """
        print('TODO!')

    @staticmethod
    def prepare_table_input(table_list_string):
        """ Подготавливает переданный через аргумент список таблиц """
        table_list = table_list_string.split(',')
        for table in table_list:
            if table not in Converter.TABLE_LIST:
                raise ValueError('Unknown table "{}"'.format(table))
        return table_list

    @staticmethod
    def get_dump_header():
        """ Сообщение в заголовок сгенерированного файла """
        header = ("-- --------------------------------------------------------\n"
                  "-- v. {}\n"
                  "-- get latest version @ https://github.com/shadz3rg/ru_address\n"
                  "-- file generated {}\n"
                  "-- --------------------------------------------------------\n")
        now = datetime.datetime.now()
        return header.format(__version__, str(now))

class Output:
    SINGLE_FILE = 0
    FILE_PER_TABLE = 1

    def __init__(self, output_path, mode):
        self.output_path = output_path
        self.mode = mode
        if mode == self.SINGLE_FILE:
            # Создаем общий для всех таблиц файл
            # В output_path уже добавлено название файла
            if os.path.isfile(output_path):
                raise FileExistsError('File already exist: {}'.format(output_path))
            filepath = output_path
            open(filepath, 'x', encoding='utf-8').close()

    def dump_filepath(self, filename, extension):
        file = '{}.{}'.format(filename, extension)
        return os.path.join(self.output_path, file)

    def open_dump_file(self, table):
        filepath = self.dump_filepath(table, 'sql')
        open_mode = 'w'
        if self.mode == self.SINGLE_FILE:
            filepath = self.output_path
            open_mode = 'a'
        return open(filepath, open_mode, encoding='utf-8')


