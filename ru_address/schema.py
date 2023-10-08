import glob
import os.path
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List
import lxml.etree as et
from ru_address import package_directory
from ru_address.source.xml import Definition
from ru_address.index import Index
from ru_address.core import Core


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
            'mysql': MyConverter,
            'psql':  PostgresConverter,
            'ch':    ClickhouseConverter,
        }


class BaseSchemaConverter(ABC):
    """
    Base converter for target platforms
    """
    def process(self, source_path: str, tables: List[str], include_keys: bool):
        output = OrderedDict()
        definitions = self.generate_definitions(source_path, Core.KNOWN_ENTITIES)
        known_tables = Core.get_known_tables()
        for table_name in tables:
            target_entity = known_tables[table_name]
            definition = definitions.get(target_entity, None)
            if definition:
                output[table_name] = self.convert_table(definition, table_name, include_keys)
        return output

    def generate_definitions(self, source_path: str, entities: List[str]):
        output = OrderedDict()
        for entity in entities:
            print(entity)
            source_file = self.get_source_filepath(source_path, entity, 'xsd')
            definition = Definition(entity, source_file)
            output[entity] = definition
        return output

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

    @abstractmethod
    def convert_table(self, definition: Definition, table_name: str, include_keys: bool):
        pass

    @staticmethod
    @abstractmethod
    def get_extension() -> str:
        pass


class MyConverter(BaseSchemaConverter):
    """
    MySQL (and MySQL forks) compatible converter
    """
    def __init__(self):
        self.stylesheet_file = os.path.join(package_directory, 'resources', 'mysql.template.xsl')

    def convert_table(self, definition: Definition, table_name: str, include_keys: bool):
        stylesheet = et.parse(self.stylesheet_file)
        transform = et.XSLT(stylesheet)

        plain_table_name = transform.strparam(table_name)
        index = None
        if include_keys:
            index = transform.strparam(Index().build(definition.title_name))
        # TODO: Add INCLUDE_DROP param
        # TODO: Add TABLE_ENGINE param
        # TODO: Add TABLE_ENCODING param
        result = transform(definition.tree, table_name=plain_table_name, index=index)

        return str(result)

    @staticmethod
    def get_extension() -> str:
        return 'sql'


class PostgresConverter(BaseSchemaConverter):
    """
    PostgreSQL compatible converter
    """
    def convert_table(self, definition: Definition, table_name: str, include_keys: bool):
        raise NotImplementedError

    @staticmethod
    def get_extension() -> str:
        return 'sql'


class ClickhouseConverter(BaseSchemaConverter):
    """
    Clickhouse compatible converter
    """
    def convert_table(self, definition: Definition, table_name: str, include_keys: bool):
        raise NotImplementedError

    @staticmethod
    def get_extension() -> str:
        return 'sql'
