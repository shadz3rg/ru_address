import glob
import os.path
from abc import ABC, abstractmethod
from ru_address.source.xml import Definition, Data
from ru_address.core import Core
from ru_address.common import TableRepresentation


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
            'mysql':  MyConverter,
            'psql':  PostgresConverter,
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
        self.batch_size = int(os.environ.get("RA_BATCH_SIZE", "500"))

    @abstractmethod
    def convert_table(self, file, table_name, sub=None):
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

    @staticmethod
    @abstractmethod
    def get_representation() -> TableRepresentation:
        pass

    @abstractmethod
    def compose_dump_header(self) -> str:
        pass

    @abstractmethod
    def compose_dump_footer(self) -> str:
        pass


class MyConverter(BaseDumpConverter):
    """
    MySQL (and MySQL forks) compatible converter
    """
    def __init__(self, source_path, schema_path):
        BaseDumpConverter.__init__(self, source_path, schema_path)
        self.encoding = os.environ.get("RA_SQL_ENCODING", "utf8mb4")

    def convert_table(self, file, table_name, sub=None):
        dump_file = file

        tables = Core.get_known_tables()
        source_filepath = self.get_source_filepath(self.schema_path, tables[table_name], 'xsd')
        definition = Definition(table_name, source_filepath)

        path = self.source_path
        if sub is not None:
            path = os.path.join(self.source_path, sub)

        source_filepath = self.get_source_filepath(path, table_name, 'xml')
        data = Data(table_name, source_filepath)
        data.convert_and_dump_v2(dump_file, definition, self.batch_size, self.get_representation())

    @staticmethod
    def get_extension() -> str:
        return 'sql'

    @staticmethod
    def get_representation() -> TableRepresentation:
        def table_start_handler(table_name) -> str:
            return (
                '\n'
                f'/*!40000 ALTER TABLE `{table_name}` DISABLE KEYS */;\n'
            )

        def table_end_handler(table_name) -> str:
            return (
                f'/*!40000 ALTER TABLE `{table_name}` ENABLE KEYS */;\n'
            )

        def batch_start_handler(table_name, fields):
            field_query = "`, `".join(fields)
            return (
                f'INSERT INTO `{table_name}` (`{field_query}`) VALUES \n'
            )

        return TableRepresentation(table_start_handler=table_start_handler, table_end_handler=table_end_handler,
                                   batch_start_handler=batch_start_handler)

    def compose_dump_header(self) -> str:
        """ Подготовка к импорту """
        header = ("/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;\n"
                  "/*!40101 SET NAMES {} */;\n"
                  "/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;\n"
                  "/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;\n")
        return header.format(self.encoding)

    def compose_dump_footer(self) -> str:
        """ Завершение импорта """
        footer = ("/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;\n"
                  "/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;\n"
                  "/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;\n")
        return footer


class PostgresConverter(BaseDumpConverter):
    def __init__(self, source_path, schema_path):
        BaseDumpConverter.__init__(self, source_path, schema_path)
        # self.encoding = os.environ.get("RA_SQL_ENCODING", "utf8mb4")

    def convert_table(self, file, table_name, sub=None):
        dump_file = file

        tables = Core.get_known_tables()
        source_filepath = self.get_source_filepath(self.schema_path, tables[table_name], 'xsd')
        definition = Definition(table_name, source_filepath)

        path = self.source_path
        if sub is not None:
            path = os.path.join(self.source_path, sub)

        source_filepath = self.get_source_filepath(path, table_name, 'xml')
        data = Data(table_name, source_filepath)
        data.convert_and_dump_v2(dump_file, definition, self.batch_size, self.get_representation())

    @staticmethod
    def get_extension() -> str:
        return 'sql'

    @staticmethod
    def get_representation() -> TableRepresentation:
        def batch_start_handler(table_name, fields):
            field_query = "\", \"".join(fields)
            return (
                f'INSERT INTO "{table_name}" ("{field_query}") VALUES \n'
            )

        return TableRepresentation(quotes="'", bool_repr=("'0'", "'1'"), batch_start_handler=batch_start_handler)

    def compose_dump_header(self) -> str:
        return ""

    def compose_dump_footer(self) -> str:
        return ""


class PlainCommaConverter(BaseDumpConverter):
    """
    CSV compatible converter
    See: https://datatracker.ietf.org/doc/html/rfc4180
    """
    def __init__(self, source_path, schema_path):
        BaseDumpConverter.__init__(self, source_path, schema_path)

    def convert_table(self, file, table_name, sub=None):
        dump_file = file

        tables = Core.get_known_tables()
        source_filepath = self.get_source_filepath(self.schema_path, tables[table_name], 'xsd')
        definition = Definition(table_name, source_filepath)

        path = self.source_path
        if sub is not None:
            path = os.path.join(self.source_path, sub)

        source_filepath = self.get_source_filepath(path, table_name, 'xml')
        data = Data(table_name, source_filepath)
        data.convert_and_dump_v2(dump_file, definition, self.batch_size, self.get_representation())

    @staticmethod
    def get_extension() -> str:
        return 'csv'

    @staticmethod
    def get_representation() -> TableRepresentation:
        return TableRepresentation(quotes="\"", delimiter=",", null_repr="\\N",
                                   row_indent="", row_parentheses=("", ""),
                                   line_ending="\n", line_ending_last="\n")

    def compose_dump_header(self) -> str:
        return ""

    def compose_dump_footer(self) -> str:
        return ""


class PlainTabConverter(BaseDumpConverter):
    """
    TSV compatible converter
    """
    def convert_table(self, file, table_name, sub=None):
        dump_file = file

        tables = Core.get_known_tables()
        source_filepath = self.get_source_filepath(self.schema_path, tables[table_name], 'xsd')
        definition = Definition(table_name, source_filepath)

        path = self.source_path
        if sub is not None:
            path = os.path.join(self.source_path, sub)

        source_filepath = self.get_source_filepath(path, table_name, 'xml')
        data = Data(table_name, source_filepath)
        data.convert_and_dump_v2(dump_file, definition, self.batch_size, self.get_representation())

    @staticmethod
    def get_extension() -> str:
        return 'tsv'

    @staticmethod
    def get_representation() -> TableRepresentation:
        return TableRepresentation(quotes="", delimiter="\t", null_repr="\\N",
                                   row_indent="", row_parentheses=("", ""),
                                   line_ending="\n", line_ending_last="\n")

    def compose_dump_header(self) -> str:
        return ""

    def compose_dump_footer(self) -> str:
        return ""
