import time
import os
import click
from ru_address.common import Common
from ru_address import __version__
from ru_address.core import Core
from ru_address.core import Output
from ru_address.errors import UnknownPlatformError
from ru_address.schema import ConverterRegistry as SchemaConverterRegistry
from ru_address.dump import ConverterRegistry as DumpConverterRegistry, regions_from_directory
from functools import update_wrapper


def command_summary(f):
    def wrapper(**kwargs):
        start_time = time.time()
        f(**kwargs)
        Common.show_memory_usage()
        Common.show_execution_time(start_time)
    return update_wrapper(wrapper, f)


@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option(__version__)
@click.option("-e", "--env", type=(str, str), multiple=True, help='Pass env-params')
@click.pass_context
def cli(_, env):
    for k, v in env:
        os.environ.setdefault(k, v)


@cli.command()
@click.option('--target', type=click.Choice(SchemaConverterRegistry.get_available_platforms()),
              default='mysql', help='Target DB')
@click.option('-t', '--table', 'tables', type=str, multiple=True, default=Core.get_known_tables().keys(),
              help='Limit table list to process')
@click.option('--no-keys', is_flag=True, help='Exclude keys && column index')
@click.argument('source_path', type=click.types.Path(exists=True, file_okay=False, readable=True))
@click.argument('output_path', type=click.types.Path(file_okay=True, readable=True, writable=True))
@command_summary
def schema(target, tables, no_keys, source_path, output_path):
    """
    Convert XSD schema into target platform definitions.
    Get latest schema @ https://fias.nalog.ru/docs/gar_schemas.zip
    """
    registry = SchemaConverterRegistry()
    _converter = registry.get_converter(target)
    if _converter is None:
        raise UnknownPlatformError()

    converter = _converter()
    output = converter.process(source_path, tables, not no_keys)
    if os.path.isdir(output_path):
        for key, value in output.items():
            f = open(os.path.join(output_path, f'{key}.{converter.get_extension()}'), "w")
            f.write(Core.compose_copyright())
            f.write(value)
            f.close()
    else:
        f = open(output_path, "w")
        f.write(Core.compose_copyright())
        f.write(''.join(output.values()))
        f.close()


@click.command()
@click.option('--target',  type=click.Choice(DumpConverterRegistry.get_available_platforms()),
              default='sql', help='Target dump format')
@click.option('-r', '--region', 'regions', type=str, multiple=True, default=[], help='Limit region list to process')
@click.option('-t', '--table', 'tables', type=str, multiple=True, default=Core.get_known_tables(), help='Limit table list to process')
@click.argument('source_path', type=click.types.Path(exists=True, file_okay=False, readable=True))
# TODO: Check is file for join SINGLE_FILE
@click.argument('output_path', type=click.types.Path(exists=True, file_okay=True, readable=True, writable=True))
# TODO: Same by default
@click.argument('schema_path', type=click.types.Path(exists=True, file_okay=False, readable=True), default=None)
@command_summary
def dump(target, regions, tables, source_path, output_path, schema_path):
    """
    Convert tables content into target platform dump file.
    """
    output = Output(output_path, Output.FILE_PER_TABLE)

    registry = DumpConverterRegistry()
    _converter = registry.get_converter(target)
    if _converter is None:
        raise UnknownPlatformError()

    converter = _converter(source_path, schema_path)

    for table_name in Core.COMMON_TABLE_LIST:
        if table_name in tables:
            Common.cli_output(f'Processing common table `{table_name}`')
            file = output.open_dump_file(table_name)
            file.write(Core.compose_copyright())
            file.write(converter.compose_dump_header())
            converter.convert_table(file, table_name)
            file.write(converter.compose_dump_footer())
            file.close()

    if len(regions) == 0:
        regions = regions_from_directory(source_path)

    for region in regions:
        Common.cli_output(f'Processing region directory `{region}`')
        for table_name in Core.REGION_TABLE_LIST:
            if table_name in tables:
                Common.cli_output(f'Processing table `{table_name}`')
                file = output.open_dump_file(table_name, region)
                file.write(Core.compose_copyright())
                file.write(converter.compose_dump_header())
                converter.convert_table(file, table_name, region)
                file.write(converter.compose_dump_footer())
                file.close()


cli.add_command(schema)
cli.add_command(dump)

if __name__ == '__main__':
    cli()
