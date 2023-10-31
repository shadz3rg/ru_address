import lxml.etree as et
from ru_address.common import TableRepresentation
from ru_address.errors import DefinitionError


class Data:
    """ Конвертирует XML данные в настраиваемый текстовый формат """
    def __init__(self, table_name, source_file, table_representation: TableRepresentation):
        self.table_name = table_name
        self.data_source = source_file
        self.table_representation = table_representation

    def convert_and_dump(self, dump_file, definition, bulk_size):
        if self.table_representation.table_start_handler:
            dump_file.write(self.table_representation.table_start_handler(self.table_name))

        table_fields = definition.get_table_fields()
        current_row = 0
        context = et.iterparse(self.data_source, events=('end',), tag=definition.get_entity_tag())

        for _, elem in context:
            content = []

            value_query_parts = []
            for field in table_fields:
                value = self.table_representation.null_repr
                if elem.get(field) is not None:
                    value = elem.get(field)
                    if value == "false":
                        value = self.table_representation.bool_repr[0]
                    elif value == "true":
                        value = self.table_representation.bool_repr[1]
                    else:
                        # SAX автоматически декодирует XML сущности, в значении могут быть кавычки и вообще что угодно
                        if self.table_representation.escape is not None:
                            value = value.translate(self.table_representation.escape)
                        value = f'{self.table_representation.quotes}{value}{self.table_representation.quotes}'
                value_query_parts.append(value)

            value_query = self.table_representation.delimiter.join(value_query_parts)

            # Формируем запрос
            until_new_bulk = current_row % bulk_size

            # Заканчиваем предыдущую строку
            if current_row != 0:
                line_ending = self.table_representation.line_ending
                if until_new_bulk == 0:
                    line_ending = self.table_representation.line_ending_last
                content.append(line_ending)

            # Начинаем новый инсерт, если нужно
            if current_row == 0 or until_new_bulk == 0:
                if self.table_representation.batch_start_handler:
                    content.append(self.table_representation.batch_start_handler(self.table_name, table_fields))

            # Данные для вставки, подходящий delimiter ставится у следующей записи
            content.append(f'{self.table_representation.row_indent}'
                           f'{self.table_representation.row_parentheses[0]}'
                           f'{value_query}'
                           f'{self.table_representation.row_parentheses[1]}')

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
            dump_file.write(self.table_representation.line_ending_last)  # Заканчиваем последний INSERT запрос

        if self.table_representation.table_end_handler:
            dump_file.write(self.table_representation.table_end_handler(self.table_name))


class Definition:
    """ Представление XML схемы для разбора данных """
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
