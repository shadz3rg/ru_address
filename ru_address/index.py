import lxml.etree as et
import os.path
from ru_address import package_directory


class Index:
    def __init__(self, stylesheet_file):
        self.stylesheet_file = stylesheet_file
        self.index_file = os.path.join(package_directory, 'resources', 'index.xml')
        self.index_tree = et.parse(self.index_file)

    def build(self, table_name):
        stylesheet = et.parse(self.stylesheet_file)
        transform = et.XSLT(stylesheet)

        plain_table_name = transform.strparam(table_name)
        result = transform(self.index_tree, table_name=plain_table_name)
        return str(result)
