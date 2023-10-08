import glob
import os.path
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List
import lxml.etree as et
from ru_address import package_directory
from ru_address.source.xml import Definition, Data
from ru_address.index import Index
from ru_address.core import Core


def regions_from_directory(source_path):
    matched = glob.glob('*', root_dir=source_path)
    return [f for f in matched if f.isnumeric()]


class ConverterRegistry:
    """
    Registered target platforms \\w linked converters.
    """
    @staticmethod
    def get_converter(alias):
        available = ConverterRegistry.get_available_platforms()
        return available.get(alias, None)

    @staticmethod
    def get_available_platforms():
        return {
            'sql':  SqlConverter,
            'csv':  PlainCommaConverter,
            'tsv':  PlainTabConverter,
        }


class BaseDumpConverter(ABC):
    """
    Base converter for target platforms
    """
    def __init__(self, source_path, schema_path):
        self.source_path = source_path
        self.schema_path = schema_path

    @abstractmethod
    def convert_table(self, file, table_name, batch_size, sub=None):
        pass

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

    @staticmethod
    @abstractmethod
    def get_extension() -> str:
        pass


class SqlConverter(BaseDumpConverter):
    """
    MySQL (and MySQL forks) compatible converter
    """
    def convert_table(self, file, table_name, batch_size, sub=None):
        dump_file = file

        tables = Core.get_known_tables()
        source_filepath = self.get_source_filepath(self.schema_path, tables[table_name], 'xsd')
        definition = Definition(table_name, source_filepath)

        path = self.source_path
        if sub is not None:
            path = os.path.join(self.source_path, sub)

        source_filepath = self.get_source_filepath(path, table_name, 'xml')
        data = Data(table_name, source_filepath)
        data.convert_and_dump_v2(dump_file, definition, batch_size)

    @staticmethod
    def get_extension() -> str:
        return 'sql'


class PlainCommaConverter(BaseDumpConverter):
    """
    PostgreSQL compatible converter
    """
    def convert_table(self, definition: Definition, table_name: str, include_keys: bool, sub=None):
        raise NotImplementedError

    @staticmethod
    def get_extension() -> str:
        return 'sql'


class PlainTabConverter(BaseDumpConverter):
    """
    Clickhouse compatible converter
    """
    def convert_table(self, definition: Definition, table_name: str, include_keys: bool, sub=None):
        raise NotImplementedError

    @staticmethod
    def get_extension() -> str:
        return 'sql'
