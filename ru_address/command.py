import time
import click
import os.path
from ru_address.converter import Converter
from ru_address.converter import Output
from ru_address.common import Common
from ru_address import __version__
from ru_address.core import Core
from ru_address.errors import UnknownPlatformError
from ru_address.schema import ConverterRegistry as SchemaConverterRegistry


# TODO: Add summary for each command
def command_summary(f):
    def wrapper(**kwargs):
        start_time = time.time()
        f(**kwargs)
        Common.show_memory_usage()
        time_measure = time.time() - start_time
        print(f"{round(time_measure, 2)} s")
    return wrapper


@click.group()
def cli():
    pass


@cli.command()
@click.option('--target', type=click.Choice(SchemaConverterRegistry.get_available_platforms()),
              default='mysql', help='Target DB')
@click.option('--table', type=str, multiple=True, default=Core.get_known_tables().keys(),
              help='Limit table list to process')
@click.option('--no-keys', is_flag=True, help='Exclude keys && column index')
# TODO Move ENCODING to ENV params
@click.option('--encoding', type=str, default='utf8mb4', help='Default table encoding')
@click.argument('source_path', type=click.types.Path(exists=True, file_okay=False, readable=True))
@click.argument('output_path', type=click.types.Path(file_okay=True, readable=True, writable=True))
def schema(target, table, no_keys, encoding, source_path, output_path):
    """
    Convert XSD schema into target platform definitions.
    Get latest schema @ https://fias.nalog.ru/docs/gar_schemas.zip
    """
    registry = SchemaConverterRegistry()
    _converter = registry.get_converter(target)
    if _converter is None:
        raise UnknownPlatformError()

    converter = _converter()
    output = converter.process(source_path, table, not no_keys)
    if os.path.isdir(output_path):
        for key, value in output.items():
            f = open(os.path.join(output_path, f'{key}.{converter.get_extension()}'), "w")
            # TODO: Add header
            f.write(value)
            f.close()
    else:
        f = open(output_path, "w")
        # TODO: Add header
        f.write(''.join(output.values()))
        f.close()


@click.command()
@click.option('--target',  type=click.Choice([Converter.SOURCE_XML, Converter.SOURCE_DBF]),
              default=Converter.SOURCE_XML, help='Target DB platform')
@click.option('--region', type=str, multiple=True, help='Limit region directory to process')
@click.option('--join', type=click.Choice([Converter.SOURCE_XML, Converter.SOURCE_DBF]),
              default=Converter.SOURCE_XML, help='Join dump into single file with given filename')
@click.option('--source', type=click.Choice([Converter.SOURCE_XML, Converter.SOURCE_DBF]),
              default=Converter.SOURCE_XML, help='Data source file format')
@click.option('--table-list', type=str, help='Comma-separated string for limiting table list to process')
@click.argument('source_path', type=click.types.Path(exists=True, file_okay=False, readable=True))
# TODO: Same by default
@click.argument('schema_source_path', type=click.types.Path(exists=True, file_okay=False, readable=True))
# TODO: Check is file for join SINGLE_FILE
@click.argument('output_path', type=click.types.Path(exists=True, file_okay=True, readable=True, writable=True))
def dump(join, source, table_list, no_data, no_definition, encoding, beta, source_path, output_path):
    """
    Convert tables content into target platform dump file.
    """
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


cli.add_command(schema)
cli.add_command(dump)

if __name__ == '__main__':
    cli()
