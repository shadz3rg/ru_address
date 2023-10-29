import os.path
from abc import ABC, abstractmethod
from collections import OrderedDict
import lxml.etree as et

from ru_address import package_directory
from ru_address.source.xml import Definition
from ru_address.errors import UnknownPlatformError
from ru_address.index import Index
from ru_address.core import Core
from ru_address.common import Common


class ConverterRegistry:
    """
    Registered target platforms \\w linked converters.
    """
    @staticmethod
    def get_converter(alias: str):
        available = ConverterRegistry.get_available_platforms()
        return available.get(alias, None)

    @staticmethod
    def init_converter(alias: str):
        _converter = ConverterRegistry.get_converter(alias)
        if _converter is None:
            raise UnknownPlatformError()
        return _converter()

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
    def __init__(self, schema_stylesheet_file, index_stylesheet_file, options: dict):
        self.schema_stylesheet_file = schema_stylesheet_file
        self.index_stylesheet_file = index_stylesheet_file
        self.options = options

    def process(self, source_path: str, tables: list[str], include_keys: bool):
        output = OrderedDict()
        definitions = self.generate_definitions(source_path, Core.KNOWN_ENTITIES)
        known_tables = Core.get_known_tables()
        for table_name in tables:
            target_entity = known_tables[table_name]
            definition = definitions.get(target_entity, None)
            if definition:
                output[table_name] = self.convert_table(definition, table_name, include_keys)
        return output

    @staticmethod
    def generate_definitions(source_path: str, entities: list[str]):
        output = OrderedDict()
        for entity in entities:
            Common.cli_output(entity)
            source_file = Common.get_source_filepath(source_path, entity, 'xsd')
            definition = Definition(entity, source_file)
            output[entity] = definition
        return output

    def convert_table(self, definition: Definition, table_name: str, include_keys: bool):
        stylesheet = et.parse(self.schema_stylesheet_file)
        transform = et.XSLT(stylesheet)

        # Template variables
        options = self.options.copy()
        options['table_name'] = table_name
        options['index'] = None
        if include_keys:
            options['index'] = Index(self.index_stylesheet_file).build(definition.title_name)

        for k, v in options.items():
            options[k] = transform.strparam(v)
        result = transform(definition.tree, **options)
        return str(result)

    @staticmethod
    @abstractmethod
    def get_extension() -> str:
        pass


class MyConverter(BaseSchemaConverter):
    """
    MySQL (and MySQL forks) compatible converter
    """
    def __init__(self):
        BaseSchemaConverter.__init__(
            self,
            os.path.join(package_directory, 'resources', 'templates', 'mysql.schema.xsl'),
            os.path.join(package_directory, 'resources', 'templates', 'mysql.index.xsl'),
            {
                "include_drop": os.environ.get("RA_INCLUDE_DROP", "1"),
                "table_engine": os.environ.get("RA_TABLE_ENGINE", "MyISAM"),
            }
        )

    @staticmethod
    def get_extension() -> str:
        return 'sql'


class PostgresConverter(BaseSchemaConverter):
    """
    PostgreSQL compatible converter
    """
    def __init__(self):
        BaseSchemaConverter.__init__(
            self,
            os.path.join(package_directory, 'resources', 'templates', 'postgres.schema.xsl'),
            os.path.join(package_directory, 'resources', 'templates', 'postgres.index.xsl'),
            {
                "include_drop": os.environ.get("RA_INCLUDE_DROP", "1"),
            }
        )

    @staticmethod
    def get_extension() -> str:
        return 'sql'


class ClickhouseConverter(BaseSchemaConverter):
    """
    Clickhouse compatible converter
    """
    def __init__(self):
        BaseSchemaConverter.__init__(
            self,
            os.path.join(package_directory, 'resources', 'templates', 'clickhouse.schema.xsl'),
            os.path.join(package_directory, 'resources', 'templates', 'clickhouse.index.xsl'),
            {
                "include_drop": os.environ.get("RA_INCLUDE_DROP", "1"),
                "table_engine": os.environ.get("RA_TABLE_ENGINE", "MergeTree"),
            }
        )

    @staticmethod
    def get_extension() -> str:
        return 'sql'
