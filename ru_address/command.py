import time
import click

from ru_address.converter import Converter
from ru_address.converter import Output
from ru_address.common import Common
from . import __version__


@click.command()
@click.option('--join', type=str, help='Join dump into single file with given filename')
@click.option('--source', type=click.Choice([Converter.SOURCE_XML, Converter.SOURCE_DBF]), default=Converter.SOURCE_XML,
              help='Data source file format')
@click.option('--table-list', type=str, help='Comma-separated string for limiting table list to process')
@click.option('--no-data', is_flag=True, help='Skip table definition in resulting file')
@click.option('--no-definition', is_flag=True, help='Skip table data in resulting file')
@click.option('--encoding', type=str, default='utf8mb4', help='Default table encoding')
@click.option('--beta', is_flag=True, help='Check unstable methods')
@click.argument('source_path', type=click.types.Path(exists=True, file_okay=False, readable=True))
@click.argument('output_path', type=click.types.Path(exists=True, file_okay=False, readable=True, writable=True))
@click.version_option(version=__version__)
def cli(join, source, table_list, no_data, no_definition, encoding, beta, source_path, output_path):
    """ Подготавливает БД ФИАС для использования с SQL.
    XSD файлы и XML выгрузку можно получить на сайте ФНС https://fias.nalog.ru/Updates.aspx
    """
    start_time = time.time()

    process_tables = Converter.TABLE_LIST
    if table_list is not None:
        process_tables = Converter.prepare_table_input(table_list)

    mode = Output.FILE_PER_TABLE
    if join is not None:
        mode = Output.SINGLE_FILE

    output = Output(output_path, mode)
    converter = Converter(source, source_path, beta)

    if mode == Output.SINGLE_FILE:
        file = output.open_dump_file(join)
        file.write(Converter.get_dump_copyright())
        file.write(Converter.get_dump_header(encoding))

        for table in process_tables:
            Common.cli_output(f'Processing table `{table}`')
            file.write(Converter.get_table_separator(table))
            converter.convert_table(file, table, no_definition, no_data, 500)

        file.write(Converter.get_dump_footer())
        file.close()

    elif mode == Output.FILE_PER_TABLE:
        for table in process_tables:
            file = output.open_dump_file(output.get_table_filename(table))
            file.write(Converter.get_dump_copyright())
            file.write(Converter.get_dump_header(encoding))

            Common.cli_output(f'Processing table `{table}`')
            converter.convert_table(file, table, no_definition, no_data, 500)

            file.write(Converter.get_dump_footer())
            file.close()

    Common.show_memory_usage()
    time_measure = time.time() - start_time
    print(f"{round(time_measure, 2)} s")
