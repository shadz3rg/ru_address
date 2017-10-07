import click
import os

from . import __version__
from ru_address.converter import Converter
from ru_address.converter import Output
from ru_address.common import Common


@click.command()
@click.option('--join', type=str, help='Join dump into single file with given filename')
@click.option('--source', type=click.Choice([Converter.SOURCE_XML, Converter.SOURCE_DBF]), default=Converter.SOURCE_XML,
              help='Data source file format')
@click.option('--table-list', type=str, help='Comma-separated string for limiting table list to process')
@click.option('--no-data', is_flag=True, help='Skip table definition in resulting file')
@click.option('--no-definition', is_flag=True, help='Skip table data in resulting file')
@click.argument('source_path', type=click.types.Path(exists=True, file_okay=False, readable=True))
@click.argument('output_path', type=click.types.Path(exists=True, file_okay=False, readable=True, writable=True))
@click.version_option(version=__version__)
def cli(join, source, table_list, no_data, no_definition, source_path, output_path):
    """ Подготавливает БД ФИАС для использования с SQL.
    XSD файлы и XML выгрузку можно получить на сайте ФНС https://fias.nalog.ru/Updates.aspx
    """
    # print(join, table_list, source_path, output_path)
    process_tables = Converter.TABLE_LIST
    if table_list is not None:
        process_tables = Converter.prepare_table_input(table_list)

    mode = Output.FILE_PER_TABLE
    if join is not None:
        mode = Output.SINGLE_FILE
        output_path = os.path.join(output_path, join)

    converter = Converter(source, source_path, Output(output_path, mode))
    for table in process_tables:
        Common.cli_output('Processing table `{}`'.format(table))
        converter.convert_table(table, no_definition, no_data, 500)
    Common.show_memory_usage()
