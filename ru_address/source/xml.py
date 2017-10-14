import math
import os.path
import lxml.etree as et
from xml import sax
from ru_address.common import Common
from ru_address.common import DataSource
from ru_address import package_directory
from ru_address.index import Index


class Data:
    def __init__(self, table_name, source_file):
        self.table_name = table_name
        self.data_source = source_file

    def convert_and_dump(self, dump_file, definition, bulk_size):
        source = DataSource(self.data_source)
        parser = sax.make_parser()
        parser.setContentHandler(DataHandler(self.table_name, source, dump_file, definition.get_table_fields(), bulk_size))
        parser.parse(source)

        source.close()

    def convert_and_dump_v2(self, dump_file, definition, bulk_size):

        # Отключаем ключи перед началом импорта данных
        print('/*!40000 ALTER TABLE `{}` DISABLE KEYS */;'.format(self.table_name), file=dump_file)

        table_fields = definition.get_table_fields()
        current_row = 0
        context = et.iterparse(self.data_source, events=('end',), tag=definition.get_entity_tag())

        for event, elem in context:
            content = []

            value_query_parts = []
            for field in table_fields:
                # SAX автоматически декодирует XML сущности, ломая запрос кавычками, workaround
                # Достаточно удалить двойные т.к. в них оборачиваются SQL данные
                value = "NULL"
                if elem.get(field) is not None:
                    value = elem.get(field).replace('\\', '\\\\"').replace('"', '\\"')
                    value = '"%s"' % value
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
                field_query = "`, `".join(table_fields)
                content.append('INSERT INTO `%s` (`%s`) VALUES \n' % (self.table_name, field_query))

            # Данные для вставки, подходящий delimiter ставится у следующей записи
            content.append('\t(%s)' % value_query)

            current_row += 1
            if current_row % 10000 == 0:
                print("\r%s+ row" % current_row, end="", flush=True)

            dump_file.write(''.join(content))

            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

        # Завершаем файл
        print("")  # Перенос после прогресс-бара
        print(";", file=dump_file)  # Заканчиваем последний INSERT запрос
        # Вспомогательные запросы на манер бэкапов из phpMyAdmin
        print('/*!40000 ALTER TABLE `{}` ENABLE KEYS */;'.format(self.table_name), file=dump_file)


class DataHandler(sax.ContentHandler):
    def __init__(self, table_name, source, dump, table_fields, bulk_size):
        super().__init__()
        self.table_name = table_name
        self.source = source
        self.dump = dump
        self.table_fields = table_fields
        self.bulk_size = bulk_size

        # Отключаем ключи перед началом импорта данных
        print('/*!40000 ALTER TABLE `{}` DISABLE KEYS */;'.format(self.table_name), file=self.dump)

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
                value = '"{}"'.format(value)
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
            print('INSERT INTO `{}` (`{}`) VALUES '.format(self.table_name, field_query), file=self.dump)

        # Данные для вставки, подходящий delimiter ставится у следующей записи
        print('\t({})'.format(value_query), file=self.dump, end="")

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
        print('/*!40000 ALTER TABLE `{}` ENABLE KEYS */;'.format(self.table_name), file=self.dump)


class Definition:
    def __init__(self, table_name, source_file):
        self.table_name = table_name
        self.tree = et.parse(source_file)
        self.stylesheet_file = os.path.join(package_directory, 'resources', 'definition.xsl')
        self.table_fields = self._fetch_table_fields()
        self.entity_tag = self._fetch_entity_tag()

    def _fetch_table_fields(self):
        table_fields = []

        ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}
        table_field_elements = self.tree.findall(".//xs:attribute", ns)
        for table_field_element in table_field_elements:
            table_fields.append(table_field_element.attrib["name"])

        return table_fields

    def _fetch_entity_tag(self):
        ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}
        element = self.tree.find(".//xs:sequence/xs:element", ns)
        return element.attrib['name']

    def get_table_fields(self):
        return self.table_fields

    def get_entity_tag(self):
        return self.entity_tag

    def convert_and_dump(self, dump_file):
        stylesheet = et.parse(self.stylesheet_file)
        transform = et.XSLT(stylesheet)

        plain_table_name = transform.strparam(self.table_name)
        index = transform.strparam(Index().build(self.table_name))
        result = transform(self.tree, table_name=plain_table_name, index=index)

        dump_file.write(str(result))
