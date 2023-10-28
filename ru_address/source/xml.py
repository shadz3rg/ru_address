import math
import xml.sax
import lxml.etree as et
from ru_address.common import Common
from ru_address.common import DataSource
from ru_address.common import TableRepresentation
from ru_address.errors import DefinitionError


class Data:
    """XML data file handler"""
    def __init__(self, table_name, source_file):
        self.table_name = table_name
        self.data_source = source_file

    def convert_and_dump(self, dump_file, definition, bulk_size):
        source = DataSource(self.data_source)
        parser = xml.sax.make_parser()
        parser.setContentHandler(DataHandler(self.table_name, source, dump_file,
                                             definition.get_table_fields(), bulk_size))
        parser.parse(source)

        source.close()

    def convert_and_dump_v2(self, dump_file, definition, bulk_size, table_representation: TableRepresentation):

        if table_representation.table_start_handler:
            dump_file.write(table_representation.table_start_handler(self.table_name))

        table_fields = definition.get_table_fields()
        current_row = 0
        context = et.iterparse(self.data_source, events=('end',), tag=definition.get_entity_tag())

        for _, elem in context:
            content = []

            value_query_parts = []
            for field in table_fields:
                value = table_representation.null_repr
                if elem.get(field) is not None:
                    value = elem.get(field)
                    if value == "false":
                        value = table_representation.bool_repr[0]
                    elif value == "true":
                        value = table_representation.bool_repr[1]
                    else:
                        # SAX автоматически декодирует XML сущности, ломая запрос кавычками, workaround
                        # Достаточно удалить двойные т.к. в них оборачиваются SQL данные
                        # value = value.replace('\\', '\\\\"').replace('"', '\\"')  # TODO Quotes
                        value = f'{table_representation.quotes}{value}{table_representation.quotes}'
                value_query_parts.append(value)

            value_query = table_representation.delimiter.join(value_query_parts)

            # Формируем запрос
            until_new_bulk = current_row % bulk_size

            # Заканчиваем предыдущую строку
            if current_row != 0:
                line_ending = table_representation.line_ending
                if until_new_bulk == 0:
                    line_ending = table_representation.line_ending_last
                content.append(line_ending)

            # Начинаем новый инсерт, если нужно
            if current_row == 0 or until_new_bulk == 0:
                if table_representation.batch_start_handler:
                    content.append(table_representation.batch_start_handler(self.table_name, table_fields))

            # Данные для вставки, подходящий delimiter ставится у следующей записи
            content.append(f'{table_representation.row_indent}'
                           f'{table_representation.row_parentheses[0]}'
                           f'{value_query}'
                           f'{table_representation.row_parentheses[1]}')

            current_row += 1
            if current_row % 10000 == 0:
                print(f"\r{current_row}+ row", end="", flush=True)

            dump_file.write(''.join(content))

            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

        # Завершаем файл
        print("")  # Перенос после прогресс-бара
        if current_row != 0:
            dump_file.write(table_representation.line_ending_last)  # Заканчиваем последний INSERT запрос

        if table_representation.table_end_handler:
            dump_file.write(table_representation.table_end_handler(self.table_name))

    def convert_and_dump_v3(self, dump_file, definition, bulk_size):

        # Отключаем ключи перед началом импорта данных
        # print(f'/*!40000 ALTER TABLE `{self.table_name}` DISABLE KEYS */;', file=dump_file)

        table_fields = definition.get_table_fields()
        current_row = 0
        context = et.iterparse(self.data_source, events=('end',), tag=definition.get_entity_tag())

        for _, elem in context:
            content = []

            value_query_parts = []
            for field in table_fields:
                # SAX автоматически декодирует XML сущности, ломая запрос кавычками, workaround
                # Достаточно удалить двойные т.к. в них оборачиваются SQL данные
                value = "NULL"
                if elem.get(field) is not None:
                    value = elem.get(field)
                    if value == "true":
                        value = "'1'"
                    elif value == "false":
                        value = "'0'"
                    else:
                        value = value.replace('\\', '\\\\"').replace('"', '\\"')
                        value = f'\'{value}\''
                value_query_parts.append(value)

            value_query = ', '.join(value_query_parts)

            # Формируем запрос
            until_new_bulk = current_row % bulk_size

            # Заканчиваем предыдущую строку
            if current_row != 0:
                line_ending = ',\n'
                if until_new_bulk == 0:
                    line_ending = ';\n'
                content.append(line_ending)

            # Начинаем новый инсерт, если нужно
            if current_row == 0 or until_new_bulk == 0:
                field_query = "\", \"".join(table_fields)
                content.append(f'INSERT INTO "{self.table_name}" ("{field_query}") VALUES \n')

            # Данные для вставки, подходящий delimiter ставится у следующей записи
            content.append(f'\t({value_query})')

            current_row += 1
            if current_row % 10000 == 0:
                print(f"\r{current_row}+ row", end="", flush=True)

            dump_file.write(''.join(content))

            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

        # Завершаем файл
        print("")  # Перенос после прогресс-бара
        if current_row != 0:
            print(";", file=dump_file)  # Заканчиваем последний INSERT запрос
        # Вспомогательные запросы на манер бэкапов из phpMyAdmin
        # print(f'/*!40000 ALTER TABLE `{self.table_name}` ENABLE KEYS */;', file=dump_file)


class DataHandler(xml.sax.handler.ContentHandler):
    """XML data content handler"""
    def __init__(self, table_name, source, dump, table_fields, bulk_size):
        super().__init__()
        self.table_name = table_name
        self.source = source
        self.dump = dump
        self.table_fields = table_fields
        self.bulk_size = bulk_size

        # Отключаем ключи перед началом импорта данных
        print(f'/*!40000 ALTER TABLE `{self.table_name}` DISABLE KEYS */;', file=self.dump)

        # Для XML обработчика
        self.tree_depth = 0
        self.current_row = 0
        self.processed_percent = 0

    def startElement(self, name, attrs):
        # Псевдо-дерево, нужно пропустить корневой элемент
        if self.tree_depth == 0:
            self.tree_depth += 1
            return

        self.tree_depth += 1

        # Подготавливаем поля
        value_query_parts = []
        for field in self.table_fields:
            # SAX автоматически декодирует XML сущности, ломая запрос кавычками, workaround
            # Достаточно удалить двойные т.к. в них оборачиваются SQL данные
            value = "NULL"
            if attrs.get(field) is not None:
                value = attrs.get(field).replace('\\', '\\\\"').replace('"', '\\"')
                value = f'"{value}"'
            value_query_parts.append(value)

        value_query = ', '.join(value_query_parts)

        # Формируем запрос
        until_new_bulk = self.current_row % self.bulk_size

        # Заканчиваем предыдущую строку
        if self.current_row != 0:
            line_ending = ', '
            if until_new_bulk == 0:
                line_ending = '; '
            print(line_ending, file=self.dump)

        # Начинаем новый инсерт, если нужно
        if self.current_row == 0 or until_new_bulk == 0:
            field_query = "`, `".join(self.table_fields)
            print(f'INSERT INTO `{self.table_name}` (`{field_query}`) VALUES ', file=self.dump)

        # Данные для вставки, подходящий delimiter ставится у следующей записи
        print(f'\t({value_query})', file=self.dump, end="")

        self.current_row += 1


        # Вывод прогресса
        current_percent = math.ceil(self.source.percentage)
        if current_percent > self.processed_percent:
            Common.update_progress(current_percent / 100)

        self.processed_percent = current_percent

    def endElement(self, name):
        self.tree_depth -= 1

    def endDocument(self):
        Common.update_progress(1)
        print("")  # Перенос после прогресс-бара
        print(";", file=self.dump)  # Заканчиваем последний INSERT запрос
        # Вспомогательные запросы на манер бэкапов из phpMyAdmin
        print(f'/*!40000 ALTER TABLE `{self.table_name}` ENABLE KEYS */;', file=self.dump)


class Definition:
    """XML table schema handler"""
    def __init__(self, title_name, source_file):
        self.title_name = title_name
        self.tree = et.parse(source_file)
        self.collection_tag = self._fetch_collection_tag()
        self.entity_tag = self._fetch_entity_tag()
        self.table_fields = self._fetch_table_fields()

    def _fetch_table_fields(self):
        table_fields = []

        namespace = {'xs': 'http://www.w3.org/2001/XMLSchema'}
        table_field_elements = self.tree.findall(".//xs:attribute", namespace)
        for table_field_element in table_field_elements:
            table_fields.append(table_field_element.attrib["name"])

        return table_fields

    def _fetch_collection_tag(self):
        namespace = {'xs': 'http://www.w3.org/2001/XMLSchema'}
        element = self.tree.find("/xs:element[@name]", namespace)
        return element.attrib['name']

    def _fetch_entity_tag(self):
        namespace = {'xs': 'http://www.w3.org/2001/XMLSchema'}
        element = self.tree.find(".//xs:sequence/xs:element[@name]", namespace)
        if element is not None:
            return element.attrib['name']

        element = self.tree.find(".//xs:sequence/xs:element[@ref]", namespace)
        if element is not None:
            return element.attrib['ref']

        raise DefinitionError

    def get_table_fields(self):
        return self.table_fields

    def get_entity_tag(self):
        return self.entity_tag
