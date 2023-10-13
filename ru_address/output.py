import os
from abc import ABC, abstractmethod
from ru_address.core import Core
from ru_address.common import Common


class OutputRegistry:
    @staticmethod
    def get_output(alias):
        available = OutputRegistry.get_available_modes()
        return available.get(alias, None)

    @staticmethod
    def get_available_modes():
        return {
            'direct':       DirectOutput,
            'per_region':   RegionOutput,
            'per_table':    TableOutput,
            'region_tree':  RegionTreeOutput,
        }


class BaseOutput(ABC):
    def __init__(self, converter, output_path):
        self.converter = converter
        self.output_path = output_path

    @abstractmethod
    def write(self, tables, regions):
        pass


class DirectOutput(BaseOutput):
    def write(self, tables, regions):
        # self.output_path is file here
        f = open(self.output_path, "w", encoding='utf-8')
        f.write(Core.compose_copyright())
        f.write(self.converter.compose_dump_header())
        for table_name in Core.COMMON_TABLE_LIST:
            if table_name in tables:
                Common.cli_output(f'Processing table `{table_name}`')
                f.write("\n")
                f.write(Core.compose_table_separator(table_name))
                self.converter.convert_table(f, table_name, None)
        for region in regions:
            Common.cli_output(f'Processing region directory `{region}`')
            for table_name in Core.REGION_TABLE_LIST:
                if table_name in tables:
                    Common.cli_output(f'Processing table `{table_name}`')
                    f.write("\n")
                    f.write(Core.compose_table_separator(table_name, region))
                    self.converter.convert_table(f, table_name, region)
        f.write("\n")
        f.write(self.converter.compose_dump_footer())
        f.close()


class RegionOutput(BaseOutput):
    def write(self, tables, regions):
        for table_name in Core.COMMON_TABLE_LIST:
            if table_name in tables:
                Common.cli_output(f'Processing table `{table_name}`')
                f = open(os.path.join(self.output_path, f'{table_name}.sql',), "w", encoding='utf-8')
                f.write(Core.compose_copyright())
                f.write(self.converter.compose_dump_header())
                f.write("\n")
                f.write(Core.compose_table_separator(table_name))
                self.converter.convert_table(f, table_name, None)
                f.write("\n")
                f.write(self.converter.compose_dump_footer())
                f.close()
        for region in regions:
            Common.cli_output(f'Processing region directory `{region}`')
            f = open(os.path.join(self.output_path, f'{region}.sql',), "w", encoding='utf-8')
            f.write(Core.compose_copyright())
            f.write(self.converter.compose_dump_header())
            for table_name in Core.REGION_TABLE_LIST:
                if table_name in tables:
                    Common.cli_output(f'Processing table `{table_name}`')
                    f.write("\n")
                    f.write(Core.compose_table_separator(table_name, region))
                    self.converter.convert_table(f, table_name, region)
            f.write("\n")
            f.write(self.converter.compose_dump_footer())
            f.close()


class TableOutput(BaseOutput):
    def write(self, tables, regions):
        for table_name in Core.COMMON_TABLE_LIST:
            if table_name in tables:
                Common.cli_output(f'Processing table `{table_name}`')
                f = open(os.path.join(self.output_path, f'{table_name}.sql'), "w", encoding='utf-8')
                f.write(Core.compose_copyright())
                f.write(self.converter.compose_dump_header())
                f.write("\n")
                self.converter.convert_table(f, table_name, None)
                f.write("\n")
                f.write(self.converter.compose_dump_footer())
                f.close()
        for table_name in Core.REGION_TABLE_LIST:
            if table_name in tables:
                Common.cli_output(f'Processing table `{table_name}`')
                f = open(os.path.join(self.output_path, f'{table_name}.sql', ), "w", encoding='utf-8')
                f.write(Core.compose_copyright())
                f.write(self.converter.compose_dump_header())
                for region in regions:
                    Common.cli_output(f'Processing region directory `{region}`')
                    f.write("\n")
                    f.write(Core.compose_table_separator(table_name, region))
                    self.converter.convert_table(f, table_name, region)
                f.write("\n")
                f.write(self.converter.compose_dump_footer())
                f.close()


class RegionTreeOutput(BaseOutput):
    def write(self, tables, regions):
        for table_name in Core.COMMON_TABLE_LIST:
            if table_name in tables:
                Common.cli_output(f'Processing table `{table_name}`')
                f = open(os.path.join(self.output_path, f'{table_name}.sql'), "w", encoding='utf-8')
                f.write(Core.compose_copyright())
                f.write(self.converter.compose_dump_header())
                f.write("\n")
                self.converter.convert_table(f, table_name, None)
                f.write("\n")
                f.write(self.converter.compose_dump_footer())
                f.close()
        for region in regions:
            Common.cli_output(f'Processing region directory `{region}`')
            if not os.path.exists(os.path.join(self.output_path, region)):
                os.mkdir(os.path.join(self.output_path, region))
            for table_name in Core.REGION_TABLE_LIST:
                if table_name in tables:
                    Common.cli_output(f'Processing table `{table_name}`')
                    f = open(os.path.join(self.output_path, region, f'{table_name}.sql', ), "w", encoding='utf-8')
                    f.write(Core.compose_copyright())
                    f.write(self.converter.compose_dump_header())
                    f.write("\n")
                    f.write(Core.compose_table_separator(table_name, region))
                    self.converter.convert_table(f, table_name, region)
                    f.write("\n")
                    f.write(self.converter.compose_dump_footer())
                    f.close()
