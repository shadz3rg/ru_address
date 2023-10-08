import time
import os.path
import click
from ru_address.converter import Converter
from ru_address.converter import Output
from ru_address.common import Common
from ru_address import __version__
from ru_address.core import Core
from ru_address.errors import UnknownPlatformError
from ru_address.schema import ConverterRegistry as SchemaConverterRegistry
from ru_address.dump import ConverterRegistry as DumpConverterRegistry, regions_from_directory


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
@click.option('--target',  type=click.Choice(DumpConverterRegistry.get_available_platforms()),
              default='sql', help='Target dump format')
@click.option('--region', type=str, multiple=True, default=[], help='Limit region list to process')
@click.option('--table', type=str, multiple=True, default=Core.get_known_tables(), help='Limit table list to process')
@click.argument('source_path', type=click.types.Path(exists=True, file_okay=False, readable=True))
# TODO: Check is file for join SINGLE_FILE
@click.argument('output_path', type=click.types.Path(exists=True, file_okay=True, readable=True, writable=True))
# TODO: Same by default
@click.argument('schema_path', type=click.types.Path(exists=True, file_okay=False, readable=True), default=None)
def dump(target, region, table, source_path, output_path, schema_path):
    """
    Convert tables content into target platform dump file.
    """
    output = Output(output_path, Output.FILE_PER_TABLE)
    encoding = 'utf8mb4'

    registry = DumpConverterRegistry()
    _converter = registry.get_converter(target)
    if _converter is None:
        raise UnknownPlatformError()

    converter = _converter(source_path, schema_path)

    for table_name in Core.COMMON_TABLE_LIST:
        if table_name in table:
            Common.cli_output(f'Processing common table `{table_name}`')
            file = output.open_dump_file(table_name)
            file.write(Converter.compose_copyright())
            file.write(Converter.compose_dump_header(encoding))
            # TODO Batch size via ENV param
            converter.convert_table(file, table_name, 500)
            file.write(Converter.compose_dump_footer())
            file.close()

    if len(region) == 0:
        region = regions_from_directory(source_path)

    for _region in region:
        Common.cli_output(f'Processing region directory `{_region}`')
        for table_name in Core.REGION_TABLE_LIST:
            if table_name in table:
                Common.cli_output(f'Processing table `{table_name}`')
                file = output.open_dump_file(table_name, _region)
                file.write(Converter.compose_copyright())
                file.write(Converter.compose_dump_header(encoding))
                # TODO Batch size via ENV param
                converter.convert_table(file, table_name, 500, _region)
                file.write(Converter.compose_dump_footer())
                file.close()


cli.add_command(schema)
cli.add_command(dump)

if __name__ == '__main__':
    cli()
