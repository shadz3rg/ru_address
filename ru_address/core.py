import datetime
import os
from ru_address import __version__


class Core:
    KNOWN_ENTITIES = [
        'ADDR_OBJ',
        'ADDR_OBJ_DIVISION',
        'ADDR_OBJ_TYPES',
        'ADM_HIERARCHY',
        'APARTMENT_TYPES',
        'APARTMENTS',
        'CARPLACES',
        'CHANGE_HISTORY',
        'HOUSE_TYPES',
        'HOUSES',
        'MUN_HIERARCHY',
        'NORMATIVE_DOCS',
        'NORMATIVE_DOCS_KINDS',
        'NORMATIVE_DOCS_TYPES',
        'OBJECT_LEVELS',
        'OPERATION_TYPES',
        'PARAM',
        'PARAM_TYPES',
        'REESTR_OBJECTS',
        'ROOM_TYPES',
        'ROOMS',
        'STEADS',
    ]

    COMMON_TABLE_LIST = {
        'ADDHOUSE_TYPES': 'HOUSE_TYPES',
        'ADDR_OBJ_TYPES': 'ADDR_OBJ_TYPES',
        'APARTMENT_TYPES': 'APARTMENT_TYPES',
        'HOUSE_TYPES': 'HOUSE_TYPES',
        'NORMATIVE_DOCS_KINDS': 'NORMATIVE_DOCS_KINDS',
        'NORMATIVE_DOCS_TYPES': 'NORMATIVE_DOCS_TYPES',
        'OBJECT_LEVELS': 'OBJECT_LEVELS',
        'OPERATION_TYPES': 'OPERATION_TYPES',
        'PARAM_TYPES': 'PARAM_TYPES',
        'ROOM_TYPES': 'ROOM_TYPES',
    }

    REGION_TABLE_LIST = {
        'ADDR_OBJ': 'ADDR_OBJ',
        'ADDR_OBJ_DIVISION': 'ADDR_OBJ_DIVISION',
        'ADDR_OBJ_PARAMS': 'PARAM',
        'ADM_HIERARCHY': 'ADM_HIERARCHY',
        'APARTMENTS': 'APARTMENTS',
        'APARTMENTS_PARAMS': 'PARAM',
        'CARPLACES': 'CARPLACES',
        'CARPLACES_PARAMS': 'PARAM',
        'CHANGE_HISTORY': 'CHANGE_HISTORY',
        'HOUSES': 'HOUSES',
        'HOUSES_PARAMS': 'PARAM',
        'MUN_HIERARCHY': 'MUN_HIERARCHY',
        'NORMATIVE_DOCS': 'NORMATIVE_DOCS',
        'REESTR_OBJECTS': 'REESTR_OBJECTS',
        'ROOMS': 'ROOMS',
        'ROOMS_PARAMS': 'PARAM',
        'STEADS': 'STEADS',
        'STEADS_PARAMS': 'PARAM',
    }

    @staticmethod
    def get_known_tables():
        return Core.COMMON_TABLE_LIST | Core.REGION_TABLE_LIST

    @staticmethod
    def compose_copyright():
        """ Сообщение в заголовок сгенерированного файла """

        now = datetime.datetime.now()
        version_string = f'v{__version__} -- get latest version @ https://github.com/shadz3rg/ru_address'
        generation_ts = f'generation timestamp: {str(now)}'

        header = (
            "-- {} --\n"
            "-- {} --\n"
            "-- {}{} --\n"
            "-- {} --\n\n"
        )

        return header.format(
            '-' * len(version_string),
            version_string,
            generation_ts,
            ' ' * (len(version_string) - len(generation_ts)),
            '-' * len(version_string)
        )


class Output:
    """Conversion result helper"""
    SINGLE_FILE = 0
    FILE_PER_TABLE = 1

    def __init__(self, output_path, mode):
        self.output_path = output_path
        self.mode = mode

    def open_dump_file(self, table_name, sub_dir=None):
        filename = f'{table_name}.sql'
        if sub_dir:
            if not os.path.exists(os.path.join(self.output_path, sub_dir)):
                os.mkdir(os.path.join(self.output_path, sub_dir))
            filepath = os.path.join(self.output_path, sub_dir, filename)
        else:
            filepath = os.path.join(self.output_path, filename)
        return open(filepath, 'w', encoding='utf-8')
